import json
import requests
import sys

from datetime import datetime

class HyriseConnection(object):

    def __init__(self, host="localhost", port=5000, debuglog=None):
        self._host = host
        self._port = port
        self._context = None
        self._url = "http://%s:%s/" % (host, port)
        self.header = None
        self._result = None
        self.debuglog = "{}_{}.log".format(debuglog, datetime.now().strftime('%m_%d_%H_%M'))
        self.last_query = None
        self.counter = 0
        if self.debuglog:
            with open(self.debuglog,'w') as logfile:
                logfile.write('[')

    def query(self, querystr, paramlist=None, commit=False):
        q = querystr
        if paramlist:
            assert isinstance(paramlist, dict)
            for k,v in paramlist.iteritems():
                if v == True:
                    v = 1;
                elif v == False:
                    v = 0;
            q = q % paramlist

        self.last_query = q
        r = self.query_raw(query=q, context=self._context, commit=commit)
        json_response = json.loads(r)

        if self.debuglog:
            try:
                with open(self.debuglog,'a') as logfile:
                    logfile.write(json.dumps({'id':self.counter, 'query':q, 'time':json_response['performanceData'][-1]['endTime'], 'performancedata':json_response['performanceData']}) + ',\n')
                    self.counter += 1
            except:
                import pdb; pdb.set_trace()
                raise
                #pass

        sys.stdout.write('.')

        if json_response.has_key('error'):
            print "#######QueryError#########"
            print r
            sys.exit(-1)


        self._context = json_response.get("session_context", None)

        self._result = json_response.get('rows', None)
        self.header = json_response.get('header', None)
        sys.stdout.flush()

        #return json_response

    def query_raw(self, query, context, commit=False):
        payload = { "query" : query }
        if context:
            payload["session_context"] = context
        if commit:
            payload["autocommit"] = "true"
        result = requests.post(self._url + "query/",
                               data = payload)
        return result.text

    def commit(self):
        if not self._context:
            raise Exception("Should not commit without running context")
        r = self.query("""{"operators": {"cm": {"type": "Commit"}}}""")
        self._context = None
        return r

    def rollback(self):
        if not self._context:
            raise Exception("Should not rollback without running context")
        r = self.query("""{"operators": {"rb": {"type": "Rollback"}}}""")
        self._context = None
        return r

    def runningTransactions(self):
        return json.loads(requests.get(self._server_base_url + "status/tx").text)

    def fetchone(self, column=None):
        if self._result:
            r = self._result.pop()
            if column:
                return r[self.header.index(column)]
            return r
        print "Last Query returned None:"
        import pdb; pdb.set_trace()
        return None

    def fetchone_as_dict(self):
        if self._result:
            return dict(zip(self.header, self._result.pop()))
        print "Last Query returned None:"
        import pdb; pdb.set_trace()
        return None

    def fetchall(self):
        if self._result:
            temp = self._result
            self._result = None
            return temp
        return None

    def fetchall_as_dict(self):
        if self._result:
            r = [dict(zip(self.header, cur_res)) for cur_res in self._result]
            return r
            self._result = None
        return None
