from JumpScale import j
import psycopg2
import time
import datetime
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
import binascii
import copy

# import calendar
# from htmllib import HTMLParser
# from formatter import AbstractFormatter, DumbWriter
# from io import StringIO
# import JumpScale.lib.html

class PostgresqlFactory:
    """
    """

    def __init__(self):
        self.__jslocation__ = "j.clients.postgres"
        self.clients={}

    def getClient(self,ipaddr="localhost",port=5432,login="postgres",passwd="rooter",dbname="template"):
        key="%s_%s_%s_%s_%s"%(ipaddr,port,login,passwd,dbname)
        if key not in self.clients:
            self.clients[key]= PostgresClient(ipaddr,port,login,passwd,dbname)
        return self.clients[key]


    def createdb(self,db,ipaddr="localhost",port=5432,login="postgres",passwd="rooter"):
        client=psycopg2.connect("dbname='%s' user='%s' host='%s' password='%s' port='%s'"%("template1",login,ipaddr,passwd,port))
        cursor= client.cursor()
        client.set_isolation_level(0)
        try:
            cursor.execute("create database %s;"%db)
        except Exception as e:
            if str(e).find("already exists")!=-1:
                pass
            else:
                raise j.exceptions.RuntimeError(e)
        client.set_isolation_level(1)

    def dropdb(self,db,ipaddr="localhost",port=5432,login="postgres",passwd="rooter"):
        args={}
        args["db"]=db
        args["port"]=port
        args["login"]=login
        args["passwd"]=passwd
        args["ipaddr"]=ipaddr
        args["dbname"]=db
        cmd="cd /opt/postgresql/bin;./dropdb -U %(login)s -h %(ipaddr)s -p %(port)s %(dbname)s"%(args)
        # print cmd
        j.sal.process.execute(cmd,outputToStdout=False,die=False)


class PostgresClient:

    def __init__(self,ipaddr,port,login,passwd,dbname):
        self.ipaddr=ipaddr
        self.port=port
        self.login=login
        self.passwd=passwd
        self.dbname=dbname
        self.client=psycopg2.connect("dbname='%s' user='%s' host='%s' password='%s' port='%s'"%(dbname,login,ipaddr,passwd,port))
        self.cursor=None

    def getcursor(self):
        self.cursor= self.client.cursor()

    def execute(self,sql):
        if self.cursor==None:
            self.getcursor()
        return self.cursor.execute(sql)


    def initsqlalchemy(self):
        """
        usage

        base,session=client.initsqlalchemy()
        session.add(base.classes.address(email_address="foo@bar.com", user=(base.classes.user(name="foo")))
        session.commit()

        """
        Base = automap_base()

        # engine, suppose it has two tables 'user' and 'address' set up
        engine = create_engine("postgresql://%(login)s:%(passwd)s@%(ipaddr)s:%(port)s/%(dbname)s"%self.__dict__)

        # reflect the tables
        Base.prepare(engine, reflect=True)

        session = Session(engine)

        return Base,session

    def dump(self,path,tablesIgnore=[]):
        args=copy.copy(self.__dict__)
        j.sal.fs.createDir(path)
        base,session=self.initsqlalchemy()

        args["path"]="%s/_schema.sql"%(path)
        cmd="cd /opt/postgresql/bin;./pg_dump -U %(login)s -h %(ipaddr)s -p %(port)s -s -O -d %(dbname)s -w > %(path)s"%(args)
        # print cmd
        j.sal.process.execute(cmd,outputToStdout=False)

        for name,obj in list(base.classes.items()):
            if name in tablesIgnore:
                continue
            print("process table:%s"%name)
            args["table"]=name
            args["path"]="%s/%s.sql"%(path,name)
            #--quote-all-identifiers
            cmd="cd /opt/postgresql/bin;./pg_dump -U %(login)s -h %(ipaddr)s -p %(port)s -t %(table)s -a -b --column-inserts -d %(dbname)s -w > %(path)s"%(args)
            # print cmd
            j.sal.process.execute(cmd,outputToStdout=False)

    def restore(self,path,tables=[],schema=True):
        if not j.sal.fs.exists(path=path):
            raise j.exceptions.Input("cannot find path %s to import from."%path)
        args=copy.copy(self.__dict__)
        if schema:
            args["base"]=path
            # cmd="cd /opt/postgresql/bin;./pg_restore -1 -e -s -U %(login)s -h %(ipaddr)s -p %(port)s %(base)s/_schema.sql"%(args)
            cmd="cd /opt/postgresql/bin;./psql -U %(login)s -h %(ipaddr)s -p %(port)s -d %(dbname)s < %(base)s/_schema.sql"%(args)
            j.sal.process.execute(cmd,outputToStdout=False)

        for item in j.sal.fs.listFilesInDir(path, recursive=False, filter="*.sql",followSymlinks=True, listSymlinks=True):
            name=j.sal.fs.getBaseName(item).replace(".sql","")
            if name.find("_")==0:
                continue
            if name in tables or tables==[]:
                args["path"]=item
                # cmd="cd /opt/postgresql/bin;./pg_restore -1 -e -U %(login)s -h %(ipaddr)s -p %(port)s %(path)s"%(args)
                cmd="cd /opt/postgresql/bin;./psql -1 -U %(login)s -h %(ipaddr)s -p %(port)s -d %(dbname)s < %(path)s"%(args)
                j.sal.process.execute(cmd,outputToStdout=False)

    def dumpall2hrd(self,path,tablesIgnore=[],fieldsIgnore={},fieldsId={},fieldRewriteRules={},fieldsBinary={}):
        """
        @param fieldsIgnore is dict, with key the table & field the field to ignore
        @param fieldsId is dict, with key the table & field which needs to be the id (will become name of hrd)
        @param fieldRewriteRules is dict, with key the table & value is a function which converts the name of the field (when key=* then for all tables)

        """
        j.sal.fs.createDir(path)
        base,session=self.initsqlalchemy()
        for name,obj in list(base.classes.items()):
            out=""
            if name in tablesIgnore:
                continue
            print("process table:%s"%name)
            j.sal.fs.createDir("%s/%s"%(path,name))
            for record in session.query(obj):
                r=record.__dict__
                idfound=None
                for name2,val in list(r.items()):
                    if name in fieldsIgnore:
                        if name2 in fieldsIgnore[name]:
                            continue
                    if name2[0]=="_":
                        continue

                    if name in fieldsId:
                        if name2 == fieldsId[name]:
                            idfound=name2
                        else:
                            if isinstance( fieldsId[name],list):
                                j.application.break_into_jshell("DEBUG NOW complete code, we need to aggregate key from 2 fields ")
                    elif name2.lower()=="name":
                        idfound=name2
                    elif name2.lower()=="id":
                        idfound=name2
                    elif name2.lower()=="uuid":
                        idfound=name2
                    elif name2.lower()=="guid":
                        idfound=name2
                    elif name2.lower()=="oid":
                        idfound=name2


                    if name in fieldRewriteRules:
                        name2=fieldRewriteRules[name](name2)
                    elif "*" in fieldRewriteRules:
                        name2=fieldRewriteRules["*"](name2)

                    if name in fieldsBinary and name2 in fieldsBinary[name]:
                        val2=binascii.b2a_qp(val)#.decode("utf8")
                        out+="%s =bqp\n%s\n#BINARYEND#########\n"%(name2,val2)
                    elif isinstance(val,int) or isinstance(val,int):
                        out+="%s = %s\n"%(name2,val)
                    elif isinstance(val,float):
                        out+="%s = %s\n"%(name2,val)
                    elif isinstance(val,str):
                        out+="%s = '%s'\n"%(name2,val)
                    elif isinstance(val,str):
                        out+="%s = '%s'\n"%(name2,val.decode("utf8", "strict"))
                    elif isinstance(val,datetime.date):
                        out+="%s = %s #%s\n"%(name2,int(time.mktime(val.timetuple())),str(val))
                    else:
                        j.application.break_into_jshell("DEBUG NOW psycopg2dumpall2hrd")

                if idfound==None:
                    j.application.break_into_jshell("DEBUG NOW could not find id for %s in psycopg2dumpall2hrd"%r)

                print("process record:%s"%r[idfound])
                hrd=j.data.hrd.get(content=out,path="%s/%s/%s.hrd"%(path,name,str(r[idfound]).replace("/","==")))
                hrd.save()


    # def _html2text(self, html):
    #     return j.tools.html.html2text(html)

    # def _postgresTimeToEpoch(self,postgres_time):
    #     if postgres_time==None:
    #         return 0
    #     postgres_time_struct = time.strptime(postgres_time, '%Y-%m-%d %H:%M:%S')
    #     postgres_time_epoch = calendar.timegm(postgres_time_struct)
    #     return postgres_time_epoch

    # def _eptochToPostgresTime(self,time_epoch):
    #     time_struct = time.gmtime(time_epoch)
    #     time_formatted = time.strftime('%Y-%m-%d %H:%M:%S', time_struct)
    #     return time_formatted

    # def deleteRow(self,tablename,whereclause):
    #     Q="DELETE FROM %s WHERE %s"%(tablename,whereclause)
    #     self.client.execute(Q)
    #     result = self.client.use_result()
    #     if result!=None:
    #         result.fetch_row()

    #     return result

    # def select1(self,tablename,fieldname,whereclause):
    #     Q="SELECT %s FROM %s WHERE %s;"%(fieldname,tablename,whereclause)
    #     result=self.queryToListDict(Q)
    #     if len(result)==0:
    #         return None
    #     else:
    #         # from IPython import embed
    #         # print "DEBUG NOW select1"
    #         # embed()

    #         return result

    # def queryToListDict(self,query):
    #     self.client.query(query)
    #     fields={}
    #     result = self.client.use_result()
    #     counter=0
    #     for field in result.describe():
    #         fields[counter]=field[0]
    #         counter+=1

    #     resultout=[]
    #     while True:
    #         row=result.fetch_row()
    #         if len(row)==0:
    #             break
    #         row=row[0]
    #         rowdict={}
    #         for colnr in range(0,len(row)):
    #             colname=fields[colnr]
    #             if colname.find("dt__")==0:
    #                 colname=colname[4:]
    #                 col=self._postgresTimeToEpoch(row[colnr])
    #             elif colname.find("id__")==0:
    #                 colname=colname[4:]
    #                 col=int(row[colnr])
    #             elif colname.find("bool__")==0:
    #                 colname=colname[6:]
    #                 col=str(row[colnr]).lower()
    #                 if col=="1":
    #                     col=True
    #                 elif col=="0":
    #                     col=False
    #                 elif col=="false":
    #                     col=False
    #                 elif col=="true":
    #                     col=False
    #                 else:
    #                     raise j.exceptions.RuntimeError("Could not decide what value for bool:%s"%col)
    #             elif colname.find("html__")==0:
    #                 colname=colname[6:]
    #                 col=self._html2text(row[colnr])
    #             else:
    #                 col=row[colnr]

    #             rowdict[colname]=col
    #         resultout.append(rowdict)

    #     return resultout
