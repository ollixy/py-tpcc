import json
import logging
import os
import sys
import urllib
import urllib2

from abstractdriver import *

SKIP = True
#SKIP = False

QUERY_FILES = {
  'DELIVERY': {'deleteNewOrder': 'Delivery-deleteNewOrder.json',
              'getCId': 'Delivery-getCId.json',
              'getNewOrder': 'Delivery-getNewOrder.json',
              'sumOLAmount': 'Delivery-sumOLAmount.json',
              'updateCustomer': 'Delivery-updateCustomer.json',
              'updateOrderLine': 'Delivery-updateOrderLine.json',
              'updateOrders': 'Delivery-updateOrders.json'},
 'NEW_ORDER': {'createNewOrder': 'NewOrder-createNewOrder.json',
               'createOrder': 'NewOrder-createOrder.json',
               'createOrderLine': 'NewOrder-createOrderLine.json',
               'getCustomer': 'NewOrder-getCustomer.json',
               'getDistrict': 'NewOrder-getDistrict.json',
               'getItemInfo': 'NewOrder-getItemInfo.json',
               'getStockInfo': 'NewOrder-getStockInfo.json',
               'getWarehouseTaxRate': 'NewOrder-getWarehouseTaxRate.json',
               'incrementNextOrderId': 'NewOrder-incrementNextOrderId.json',
               'updateStock': 'NewOrder-updateStock.json'},
 'ORDER_STATUS': {'getCustomerByCustomerId': 'OrderStatus-getCustomerByCId.json',
                  'getCustomersByLastName': 'OrderStatus-getCustomersByLastName.json',
                  'getLastOrder': 'OrderStatus-getLastOrder.json',
                  'getOrderLines': 'OrderStatus-getOrderLines.json'},
 'PAYMENT': {'getCustomerByCustomerId': 'Payment-getCustomerByCId.json',
             'getCustomersByLastName': 'Payment-getCustomersByLastName.json',
             'getDistrict': 'Payment-getDistrict.json',
             'getWarehouse': 'Payment-getWarehouse.json',
             'insertHistory': 'Payment-insertHistory.json',
             'updateBCCustomer': 'Payment-updateBCCustomer.json',
             'updateDistrictBalance': 'Payment-updateDistrictBalance.json',
             'updateGCCustomer': 'Payment-updateGCCustomer.json',
             'updateWarehouseBalance': 'Payment-updateWarehouseBalance.json'},
 'STOCK_LEVEL': {'getOId': 'StockLevel-getOId.json',
                 'getStockCount': 'StockLevel-getStockCount.json'}

}

HEADERS = {
"CUSTOMER":"""C_ID|C_D_ID|C_W_ID|C_FIRST|C_MIDDLE|C_LAST|C_STREET_1|C_STREET_2|C_CITY|C_STATE|C_ZIP|C_PHONE|C_SINCE|C_CREDIT|C_CREDIT_LIM|C_DISCOUNT|C_BALANCE|C_YTD_PAYMENT|C_PAYMENT_CNT|C_DELIVERY_CNT|C_DATA
INTEGER|INTEGER|INTEGER|STRING|STRING|STRING|STRING|STRING|STRING|STRING|STRING|STRING|STRING|STRING|FLOAT|FLOAT|FLOAT|FLOAT|INTEGER|INTEGER|STRING
0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R
""",

"DISTRICT":"""D_ID|D_W_ID|D_NAME|D_STREET_1|D_STREET_2|D_CITY|D_STATE|D_ZIP|D_TAX|D_YTD|D_NEXT_O_ID
INTEGER|INTEGER|STRING|STRING|STRING|STRING|STRING|STRING|FLOAT|FLOAT|INTEGER
0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R
""",

"HISTORY":"""H_C_ID|H_C_D_ID|H_C_W_ID|H_D_ID|H_W_ID|H_DATE|H_AMOUNT|H_DATA
INTEGER|INTEGER|INTEGER|INTEGER|INTEGER|STRING|FLOAT|STRING
0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R
""",

"ITEM":"""I_ID|I_IM_ID|I_NAME|I_PRICE|I_DATA
INTEGER|INTEGER|STRING|FLOAT|STRING
0_R|0_R|0_R|0_R|0_R
""",

"NEW_ORDER":"""NO_W_ID|NO_D_ID|NO_O_ID
INTEGER|INTEGER|INTEGER
0_R|0_R|0_R
""",

"ORDER_LINE":"""OL_O_ID|OL_D_ID|OL_W_ID|OL_NUMBER|OL_I_ID|OL_SUPPLY_W_ID|OL_DELIVERY_D|OL_QUANTITY|OL_AMOUNT|OL_DIST_INFO
INTEGER|INTEGER|INTEGER|INTEGER|INTEGER|INTEGER|STRING|INTEGER|FLOAT|STRING
0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R
""",

"ORDERS":"""O_ID|O_D_ID|O_W_ID|O_C_ID|O_ENTRY_D|O_CARRIER_ID|O_OL_CNT|O_ALL_LOCAL
INTEGER|INTEGER|INTEGER|INTEGER|STRING|INTEGER|INTEGER|INTEGER
0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R
""",

"STOCK":"""S_I_ID|S_W_ID|S_QUANTITY|S_DIST_01|S_DIST_02|S_DIST_03|S_DIST_04|S_DIST_05|S_DIST_06|S_DIST_07|S_DIST_08|S_DIST_09|S_DIST_10|S_YTD|S_ORDER_CNT|S_REMOTE_CNT|S_DATA
INTEGER|INTEGER|INTEGER|STRING|STRING|STRING|STRING|STRING|STRING|STRING|STRING|STRING|STRING|INTEGER|INTEGER|INTEGER|STRING
0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R
""",

"WAREHOUSE":"""W_ID|W_NAME|W_STREET_1|W_STREET_2|W_CITY|W_STATE|W_ZIP|W_TAX|W_YTD
INTEGER|STRING|STRING|STRING|STRING|STRING|STRING|FLOAT|FLOAT
0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R|0_R
"""
}


class HyriseDriver(AbstractDriver):
    DEFAULT_CONFIG = {
        "database": ("The path to .tbl files relative to the HYRISE table directory", "tpcc/tables/" ),
        "queries": ("The path to the JSON queries", os.path.join(os.environ['HYRISE_DB_PATH'], "tpcc/queries/" )),
        "server_url" : ("The url the JSON queries are sent to (using http requests)", "http://localhost:5000/jsonQuery"),
    }
    class HyriseCursor(object):

        def __init__(self, url):
            self.header = None
            self.result = None
            self.url = url

        def execute(self, querystr, paramlist=None):
            import pdb; pdb.set_trace()
            q = querystr
            if paramlist:
                assert isinstance(paramlist, dict)
                for k,v in paramlist.iteritems():
                    if v in [True, False]:
                        v = str(v).lower()
                    if isinstance(v, datetime) or isinstance(v, str):
                        v = '"{!s}"'.format(v)
                    q = q.replace(':{}'.format(k), str(v))

            data = urllib.urlencode({'query' : q})
            response = urllib2.urlopen(self.url, data)
            r = json.loads(response.read())
            try:
                self.result = r['rows']
                self.header = r['header']
            except (KeyError, TypeError) as e:
                print "#############RequestError################"
                print "Request:"
                print q
                print "Response:"
                print e
                print r
                #sys.exit(-1)  
            return r

        def fetchone(self, column=None):
            if self.result:
                r = self.result.pop()
                if column:
                    return r[self.header.index(column)]
                return r
            return None

        def fetchone_as_dict(self):
            if self.result:
                return dict(zip(self.header, self.result.pop()))

        def fetchall(self):
            if self.result:
                temp = self.result
                self.result = None
                return temp
            return None

        def fetchall_as_dict(self):
            if self.result:
                r = [dict(zip(self.header, cur_res)) for cur_res in self.result]
                return r
                self.result = None
            return None


    class HyriseConnection(object):

        def __init__(self, url):
            self.url = url

        def cursor(self):
            return HyriseDriver.HyriseCursor(self.url)

        def commit(self):
            response = self.cursor().execute({"operators": {"cm": {"type": "Commit"}}})
            return response

        def rollback(self):
            response = self.cursor().execute({"operators": {"rb": {"type": "Rollback"}}})
            return response
   
    def __init__(self, ddl):
        super(HyriseDriver, self).__init__('hyrise', ddl)
        self.database = None
        self.tables = set()
        self.query_location = None
        self.queries = {}
        self.conn = None 
        self.cursor = None

    def makeDefaultConfig(self):
        return HyriseDriver.DEFAULT_CONFIG
    
    def loadConfig(self, config):
        for key in HyriseDriver.DEFAULT_CONFIG.keys():
            assert key in config, "Missing parameter '%s' in %s configuration" % (key, self.name)
        
        self.database = str(config["database"])
        self.query_location = str(config["queries"])
        self.conn = HyriseDriver.HyriseConnection(str(config["server_url"]))
        self.cursor = self.conn.cursor()
     
        for query_type, query_dict in QUERY_FILES.iteritems():
            for query_name, filename in query_dict.iteritems():
                with open(os.path.abspath(os.path.join(self.query_location, filename)), 'r') as jsonfile:
                    self.queries.setdefault(query_type,{})[query_name] = jsonfile.read()  

        if config["reset"] and os.path.exists(self.database):
            logging.debug("Deleting database '%s'" % self.database)
            os.unlink(self.database)

        if not SKIP:
            for k,v in HEADERS.iteritems():
                filename = os.path.join(self.database, k +'.tbl')
                with open(filename, 'w') as tblfile:
                    tblfile.write(v)
        else:
            print "SKIPPING data generation"
        

    def loadFinishItem(self):
        print """"ITEM data has been passed to the driver."""

    def loadFinishWarehouse(self, w_id):
        print """Data for warehouse {} is finished.""".format(w_id)

    def loadFinishDistrict(self, w_id, d_id):
        print """Data for district {} is finished.""".format(d_id)
        
    def loadTuples(self, tableName, tuples):
        if len(tuples) == 0: return
        assert len(tuples[0]) == len(HEADERS[tableName].split('\n')[1].split('|')), "Headerinfo for {} is wrong".format(tableName)

        filename = os.path.join(self.database, tableName +'.tbl')
        if not SKIP:
            with open(filename, 'a') as tblfile:
                for t in tuples:
                    tblfile.write('|'.join([str(i) for i in t]))
                    tblfile.write('\n')
        else:
            print "SKIPPING data generation"
        self.tables.add(tableName)
        logging.debug("Generated %d tuples for tableName %s" % (len(tuples), tableName))
        sys.stdout.write('.')
        sys.stdout.flush()
        
    def executeStart(self):
        self.cursor.execute(self.generateTableloadJson())
        
    def executeFinish(self):
        """Callback after the execution phase finishes"""
        return None
        
    def doDelivery(self, params):
        """Execute DELIVERY Transaction
        Parameters Dict:
            w_id
            o_carrier_id
            ol_delivery_d
        """    
        import pdb; pdb.set_trace()
        q = self.queries["DELIVERY"]
        
        w_id = params["w_id"]   
        o_carrier_id = params["o_carrier_id"]
        ol_delivery_d = params["ol_delivery_d"]

        result = [ ]
        for d_id in range(1, constants.DISTRICTS_PER_WAREHOUSE+1):
            self.cursor.execute(q["getNewOrder"], {'d_id':d_id, 'w_id':w_id})
            newOrder = self.cursor.fetchone_as_dict()
            if newOrder == None:
                ## No orders for this district: skip it. Note: This must be reported if > 1%
                continue
            assert len(newOrder) > 0
            no_o_id = newOrder['NO_O_ID']
            
            self.cursor.execute(q["getCId"], {'no_o_id':no_o_id, 'd_id':d_id, 'w_id':w_id})
            c_id = self.cursor.fetchone_as_dict()['C_ID']
            
            self.cursor.execute(q["sumOLAmount"], {'no_o_id':no_o_id, 'd_id':d_id, 'w_id':w_id})
            ol_total = self.cursor.fetchone_as_dict()['C_ID']

            self.cursor.execute(q["deleteNewOrder"], {'no_d_id':d_id, 'no_w_id':w_id, 'no_o_id':no_o_id})
            self.cursor.execute(q["updateOrders"], {'o_carrier_id':o_carrier_id, 'no_o_id':no_o_id, 'd_id':d_id, 'w_id':w_id})
            self.cursor.execute(q["updateOrderLine"], {'date':ol_delivery_d, 'no_o_id':no_o_id, 'd_id':d_id, 'w_id':w_id})

            # These must be logged in the "result file" according to TPC-C 2.7.2.2 (page 39)
            # We remove the queued time, completed time, w_id, and o_carrier_id: the client can figure
            # them out
            # If there are no order lines, SUM returns null. There should always be order lines.
            assert ol_total != None, "ol_total is NULL: there are no order lines. This should not happen"
            assert ol_total > 0.0

            self.cursor.execute(q["updateCustomer"], {'ol_total':ol_total, 'c_id':c_id, 'd_id':d_id, 'w_id':w_id})

            result.append((d_id, no_o_id))
        ## FOR

        self.conn.commit()
        return result
    
    def doNewOrder(self, params):
        """Execute NEW_ORDER Transaction
        Parameters Dict:
            w_id
            d_id
            c_id
            o_entry_d
            i_ids
            i_w_ids
            i_qtys
        """
        import pdb; pdb.set_trace()
        q = self.queries["NEW_ORDER"]
        
        w_id = params["w_id"]
        d_id = params["d_id"]
        c_id = params["c_id"]
        o_entry_d = params["o_entry_d"]
        i_ids = params["i_ids"]
        i_w_ids = params["i_w_ids"]
        i_qtys = params["i_qtys"]
            
        assert len(i_ids) > 0
        assert len(i_ids) == len(i_w_ids)
        assert len(i_ids) == len(i_qtys)

        all_local = True
        items = [ ]
        for i in range(len(i_ids)):
            ## Determine if this is an all local order or not
            all_local = all_local and i_w_ids[i] == w_id
            self.cursor.execute(q["getItemInfo"], {"i_id":i_ids[i]})
            items.append(self.cursor.fetchone())
        assert len(items) == len(i_ids)
        
        ## TPCC defines 1% of neworder gives a wrong itemid, causing rollback.
        ## Note that this will happen with 1% of transactions on purpose.
        for item in items:
            if len(item) == 0:
                self.conn.rollback()
                return
        ## FOR
        
        ## ----------------
        ## Collect Information from WAREHOUSE, DISTRICT, and CUSTOMER
        ## ----------------
        self.cursor.execute(q["getWarehouseTaxRate"], {"w_id":w_id})
        w_tax = self.cursor.fetchone_as_dict()['W_TAX']
        
        self.cursor.execute(q["getDistrict"], {"d_id":d_id, "w_id":w_id})
        district_info = self.cursor.fetchone_as_dict()
        d_tax = district_info['D_TAX']
        d_next_o_id = district_info['D_NEXT_O_ID']
        
        self.cursor.execute(q["getCustomer"], {"w_id":w_id, "d_id":d_id, "c_id":c_id})
        customer_info = self.cursor.fetchone_as_dict()
        c_discount = customer_info['C_DISCOUNT']

        ## ----------------
        ## Insert Order Information
        ## ----------------
        ol_cnt = len(i_ids)
        o_carrier_id = constants.NULL_CARRIER_ID
        
        self.cursor.execute(q["incrementNextOrderId"], {"d_next_o_id":d_next_o_id + 1, "d_id":d_id, "w_id":w_id})
        self.cursor.execute(q["createOrder"], {"o_id":d_next_o_id, "d_id":d_id, "w_id":w_id, "c_id":c_id, "date":o_entry_d, "o_carrier_id":o_carrier_id, "o_ol_cnt":ol_cnt, "all_local":all_local})
        self.cursor.execute(q["createNewOrder"], {"o_id":d_next_o_id, "d_id":d_id, "w_id":w_id})

        ## ----------------
        ## Insert Order Item Information
        ## ----------------
        item_data = [ ]
        total = 0
        for i in range(len(i_ids)):
            ol_number = i + 1
            ol_supply_w_id = i_w_ids[i]
            ol_i_id = i_ids[i]
            ol_quantity = i_qtys[i]

            itemInfo = items[i]
            i_name = itemInfo[1]
            i_data = itemInfo[2]
            i_price = itemInfo[0]

            self.cursor.execute(q["getStockInfo"], {"2d_id":d_id, "ol_i_id":ol_i_id, "ol_supply_w_id":ol_supply_w_id})
            stockInfo = self.cursor.fetchone()
            if len(stockInfo) == 0:
                logging.warn("No STOCK record for (ol_i_id=%d, ol_supply_w_id=%d)" % (ol_i_id, ol_supply_w_id))
                continue
            s_quantity = stockInfo[0]
            s_ytd = stockInfo[2]
            s_order_cnt = stockInfo[3]
            s_remote_cnt = stockInfo[4]
            s_data = stockInfo[1]
            s_dist_xx = stockInfo[5] # Fetches data from the s_dist_[d_id] column

            ## Update stock
            s_ytd += ol_quantity
            if s_quantity >= ol_quantity + 10:
                s_quantity = s_quantity - ol_quantity
            else:
                s_quantity = s_quantity + 91 - ol_quantity
            s_order_cnt += 1
            
            if ol_supply_w_id != w_id: s_remote_cnt += 1

            self.cursor.execute(q["updateStock"], {"s_quantity":s_quantity, "s_ytd":s_ytd, "s_order_cnt":s_order_cnt, "s_remote_cnt":s_remote_cnt, "ol_i_id":ol_i_id, "ol_supply_w_id":ol_supply_w_id})

            if i_data.find(constants.ORIGINAL_STRING) != -1 and s_data.find(constants.ORIGINAL_STRING) != -1:
                brand_generic = 'B'
            else:
                brand_generic = 'G'

            ## Transaction profile states to use "ol_quantity * i_price"
            ol_amount = ol_quantity * i_price
            total += ol_amount

            self.cursor.execute(q["createOrderLine"], {"o_id":d_next_o_id, "d_id":d_id, "w_id":w_id, "ol_number":ol_number, "ol_i_id":ol_i_id, "ol_supply_w_id":ol_supply_w_id, "date":o_entry_d, "ol_quantity":ol_quantity, "ol_amount":ol_amount, "ol_dist_info":s_dist_xx})

            ## Add the info to be returned
            item_data.append( (i_name, s_quantity, brand_generic, i_price, ol_amount) )
        ## FOR
        
        ## Commit!
        self.conn.commit()

        ## Adjust the total for the discount
        #print "c_discount:", c_discount, type(c_discount)
        #print "w_tax:", w_tax, type(w_tax)
        #print "d_tax:", d_tax, type(d_tax)
        total *= (1 - c_discount) * (1 + w_tax + d_tax)

        ## Pack up values the client is missing (see TPC-C 2.4.3.5)
        misc = [ (w_tax, d_tax, d_next_o_id, total) ]
        
        return [ customer_info, misc, item_data ]

    def doOrderStatus(self, params):
        """Execute ORDER_STATUS Transaction
        Parameters Dict:
            w_id
            d_id
            c_id
            c_last
        """
        import pdb; pdb.set_trace()
        q = self.queries["ORDER_STATUS"]
        
        w_id = params["w_id"]
        d_id = params["d_id"]
        c_id = params["c_id"]
        c_last = params["c_last"]
        
        assert w_id, pformat(params)
        assert d_id, pformat(params)

        if c_id != None:
            self.cursor.execute(q["getCustomerByCustomerId"], {"w_id":w_id, "d_id":d_id, "c_id":c_id})
            customer = self.cursor.fetchone()
        else:
            # Get the midpoint customer's id
            self.cursor.execute(q["getCustomersByLastName"], {"w_id":w_id, "d_id":d_id, "c_last":c_last})
            all_customers = self.cursor.fetchall()
            assert len(all_customers) > 0
            namecnt = len(all_customers)
            index = (namecnt-1)/2
            customer = all_customers[index]
            c_id = customer[0]
        assert len(customer) > 0
        assert c_id != None

        self.cursor.execute(q["getLastOrder"], {"w_id":w_id, "d_id":d_id, "c_id":c_id})
        order = self.cursor.fetchone()
        if order:
            self.cursor.execute(q["getOrderLines"], {"w_id":w_id, "d_id":d_id, "o_id":order[0]})
            orderLines = self.cursor.fetchall()
        else:
            orderLines = [ ]

        self.conn.commit()
        return [ customer, order, orderLines ]

    def doPayment(self, params):
        """Execute PAYMENT Transaction
        Parameters Dict:
            w_id
            d_id
            h_amount
            c_w_id
            c_d_id
            c_id
            c_lasr()t
            h_date
        """
        import pdb; pdb.set_trace()
        q = self.queries["PAYMENT"]

        w_id = params["w_id"]
        d_id = params["d_id"]
        h_amount = params["h_amount"]
        c_w_id = params["c_w_id"]
        c_d_id = params["c_d_id"]
        c_id = params["c_id"]
        c_last = params["c_last"]
        h_date = params["h_date"]

        if c_id != None:
            self.cursor.execute(q["getCustomerByCustomerId"], {"c_w_id":w_id, "c_d_id":d_id, "c_id":c_id})
            customer = self.cursor.fetchone()
        else:
            # Get the midpoint customer's id
            self.cursor.execute(q["getCustomersByLastName"], {"c_w_id":w_id, "c_d_id":d_id, "c_last":d_id})
            all_customers = self.cursor.fetchall()
            assert len(all_customers) > 0
            namecnt = len(all_customers)
            index = (namecnt-1)/2
            customer = all_customers[index]
            c_id = customer[0]
        assert len(customer) > 0
        c_balance = customer[14] - h_amount
        c_ytd_payment = customer[15] + h_amount
        c_payment_cnt = customer[16] + 1
        c_data = customer[17]

        self.cursor.execute(q["getWarehouse"], {"w_id":w_id})
        warehouse = self.cursor.fetchone()
        
        self.cursor.execute(q["getDistrict"], {"w_id":w_id, "d_id":d_id})
        district = self.cursor.fetchone()
        
        self.cursor.execute(q["updateWarehouseBalance"], {"w_ytd":h_amount, "w_id":w_id})
        self.cursor.execute(q["updateDistrictBalance"], {"d_ytd":h_amount, "w_id":w_id, "d_id":d_id})

        # Customer Credit Information
        if customer[11] == constants.BAD_CREDIT:
            newData = " ".join(map(str, [c_id, c_d_id, c_w_id, d_id, w_id, h_amount]))
            c_data = (newData + "|" + c_data)
            if len(c_data) > constants.MAX_C_DATA: c_data = c_data[:constants.MAX_C_DATA]
            self.cursor.execute(q["updateBCCustomer"], {"c_balance":c_balance, "c_ytd_payment":c_ytd_payment, "c_payment_cnt":c_payment_cnt, "c_data":c_data, "c_w_id":c_w_id, "c_d_id":c_d_id, "c_id":c_id})
        else:
            c_data = ""
            self.cursor.execute(q["updateGCCustomer"], {"c_balance":c_balance, "c_ytd_payment":c_ytd_payment, "c_payment_cnt":c_payment_cnt, "c_w_id":c_w_id, "c_d_id":c_d_id, "c_id":c_id})

        # Concatenate w_name, four spaces, d_name
        h_data = "%s    %s" % (warehouse[0], district[0])
        # Create the history record
        self.cursor.execute(q["insertHistory"], {"c_id":c_id, "c_d_id":c_d_id, "c_w_id":c_w_id, "d_id":d_id, "w_id":w_id, "h_date":h_date, "h_amount":h_amount, "h_data":h_data})

        self.conn.commit()

        # TPC-C 2.5.3.3: Must display the following fields:
        # W_ID, D_ID, C_ID, C_D_ID, C_W_ID, W_STREET_1, W_STREET_2, W_CITY, W_STATE, W_ZIP,
        # D_STREET_1, D_STREET_2, D_CITY, D_STATE, D_ZIP, C_FIRST, C_MIDDLE, C_LAST, C_STREET_1,
        # C_STREET_2, C_CITY, C_STATE, C_ZIP, C_PHONE, C_SINCE, C_CREDIT, C_CREDIT_LIM,
        # C_DISCOUNT, C_BALANCE, the first 200 characters of C_DATA (only if C_CREDIT = "BC"),
        # H_AMOUNT, and H_DATE.

        # Hand back all the warehouse, district, and customer data
        return [ warehouse, district, customer ]

    def doStockLevel(self, params):
        """Execute STOCK_LEVEL Transaction
        Parameters Dict:
            w_id
            d_id
            threshold
        """
        import pdb; pdb.set_trace()
        q = self.queries["STOCK_LEVEL"]

        w_id = params["w_id"]
        d_id = params["d_id"]
        threshold = params["threshold"]
        
        self.cursor.execute(q["getOId"], {"w_id":w_id, "d_id":d_id})
        result = self.cursor.fetchone()
        assert result
        o_id = result[0]
        
        self.cursor.execute(q["getStockCount"], {"w_id":w_id, "d_id":d_id, "o_id1":o_id, "o_id2":(o_id - 20), "w_id":w_id, "threshold":threshold})
        result = self.cursor.fetchone()
        
        self.conn.commit()
        
        return int(result[0])

    def generateTableloadJson(self):
        parts = []
        loadstr = """
            {
                "operators" : {
            """
        if not self.tables:
            import pdb; pdb.set_trace()
            tbldir = os.path.join(os.environ['HYRISE_DB_PATH'], self.database)
            self.tables = [ f.rstrip('.tbl') for f in os.listdir(tbldir) if os.path.isfile(os.path.join(tbldir,f)) ]

        for i ,tblname in enumerate(self.tables):
            parts.append("""
        "{}": {{
            "type": "TableLoad",
            "table": "{}",
            "filename" : "{}.tbl"
            }}
            """.format(i, tblname, os.path.join(self.database, tblname))
            )

        edgestr = ','.join('["{}","{}"]'.format(j,j+1) for j in range(len(self.tables)-1))

        loadstr = """
{{
    "operators" : {{
        {}
        }},
    "edges": [{}]
    }}""".format(',\n'.join(parts),edgestr)
                
        return loadstr

## CLAS