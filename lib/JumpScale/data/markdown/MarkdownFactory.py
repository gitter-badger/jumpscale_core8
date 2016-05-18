from JumpScale import j

from JumpScale.data.markdown.mistune import *

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

import copy


example="""
Introduction
============

PyGithub is a Python (2 and 3) library to use the `Github API v3 <http://developer.github.com/v3>`__.
With it, you can manage your `Github <http://github.com>`__ resources (repositories, user profiles, organizations, etc.) from Python scripts.

Should you have any question, any remark, or if you find a bug,
or if there is something you can do with the API but not with PyGithub,
please `open an issue <https://github.com/jacquev6/PyGithub/issues>`__.

```python
codeblock
```

| Format   | Tag example |
| -------- | ----------- |
| Headings | =heading1=<br>==heading2==<br>===heading3=== |
| New paragraph | A blank line starts a new paragraph |
| Source code block |  // all on one line<br> {{{ if (foo) bar else   baz }}} |

# header 1

## header 2

(Very short) tutorial
---------------------

First create a Github instance::


Download and install
--------------------

This package is in the `Python Package Index <http://pypi.python.org/pypi/PyGithub>`__,
so ``easy_install PyGithub`` or ``pip install PyGithub`` should be enough.
You can also clone it on `Github <http://github.com/jacquev6/PyGithub>`__.

They talk about PyGithub
------------------------

* http://stackoverflow.com/questions/10625190/most-suitable-python-library-for-github-api-v3
    * http://stackoverflow.com/questions/12379637/django-social-auth-github-authentication
        * http://www.freebsd.org/cgi/cvsweb.cgi/ports/devel/py-pygithub/
* https://bugzilla.redhat.com/show_bug.cgi?id=910565

"""


from JumpScale.data.markdown.mistune import *

class MDTable():
    def __init__(self):
        self.header=[]
        self.rows=[]
        self.type="table"

    def addHeader(self,cols):
        self.header=cols
        for nr in range(len(self.header)):
            if self.header[nr]==None or self.header[nr].strip()=="":
                self.header[nr]=" . "

    def addRow(self,cols):
        if len(cols)!=len(self.header):
            raise j.exceptions.Input("cols need to be same size as header. %s vs %s"%(len(cols),len(self.header)))
        for nr in range(len(cols)):
            if cols[nr]==None or cols[nr].strip()=="":
                cols[nr]=" . "
        self.rows.append(cols)

    def _findSizes(self):
        m=[0 for item in self.header]
        x=0
        for col in self.header:
            if len(col)>m[x]:
                m[x]=len(col)
            x+=1
        for row in self.rows:
            x=0
            for col in row:
                if len(col)>m[x]:
                    m[x]=len(col)
                x+=1
        return m

    def __repr__(self):
        def pad(text,l,add=" "):
            while(len(text)<l):
                text+=add
            return text
        pre=""
        m=self._findSizes()

        #HEADER
        x=0
        out="|"
        for col in self.header:
            col=pad(col,m[x])
            out+="%s|"%col
            x+=1
        out+="\n"

        #INTERMEDIATE
        x=0
        out+="|"
        for col in self.header:
            col=pad("",m[x],"-")
            out+="%s|"%col
            x+=1
        out+="\n"

        for row in self.rows:
            x=0
            out+="|"
            for col in row:
                col=pad(col,m[x])
                out+="%s|"%col
                x+=1
            out+="\n"

        out+="\n"
        return out

    __str__=__repr__

class MDHeader():
    def __init__(self,level,title):
        self.level=level
        self.title=title
        self.type="header"

    def __repr__(self):
        pre=""
        for i in range(self.level):
            pre+="#"
        return "%s %s"%(pre,self.title)

    __str__=__repr__

class MDListItem():
    def __init__(self,level,text):
        self.level=level
        self.text=text
        self.type="list"

    def __repr__(self):
        pre=""
        if self.level>1:
            for i in range(self.level-1):
                pre+="    "
            return "%s %s"%(pre,self.text)
        else:
            return " %s"%(self.text)

    __str__=__repr__

class MDComment():
    def __init__(self,text):
        self.text=text
        self.type="comment"

    def __repr__(self):
        out="<!--\n%s\n-->\n"%self.text

    __str__=__repr__

class MDComment1Line():
    def __init__(self,text):
        self.text=text
        self.type="comment1line"

    def __repr__(self):
        out="<!--%s-->\n"%self.text
        return out

    __str__=__repr__

class MDBlock():
    def __init__(self,text):
        self.text=text
        self.type="block"

    def __repr__(self):
        out=self.text
        if len(out)>0:
            if out[-1]!="\n":
                out+="\n"
            if out[-2]!="\n":
                out+="\n"
        return out

    __str__=__repr__

class MDCode():
    def __init__(self,text,lang):
        self.text=text
        self.type="code"
        self.lang=lang

    def __repr__(self):
        out=self.text
        code="\n```$lang\n$code\n```\n"
        if self.lang==None:
            self.lang=""
        code=code.replace("$lang",self.lang)
        code=code.replace("$code",self.text)
        return code

    __str__=__repr__

class MDData():
    def __init__(self,ddict,name="",guid=""):
        self.name=name
        self.type="data"
        self.ddict=ddict
        self._hash=""
        if name=="":
            if "name" in ddict:
                self.name=ddict["name"]
            else:
                raise j.exceptions.Input("name cannot be empty and could not be retrieved from dict")
        else:
            self.name=name

        if guid=="":
            if "guid" in ddict:
                self.guid=ddict["guid"]
            elif "id" in ddict:
                self.guid=ddict["id"]
            elif "name" in ddict:
                self.guid=ddict["name"]
            else:
                raise j.exceptions.Input("guid cannot be empty and could not be retrieved from dict")
        else:
            self.guid=guid

    @property
    def datahr(self):
        return j.data.serializer.yaml.dumps(self.ddict)

    @property
    def hash(self):
        if self._hash=="":
            json=j.data.serializer.json.dumps(self.ddict,True,True)
            self._hash=j.data.hash.md5_string(json)
        return self._hash


    def __repr__(self):
        out="<!--data|%s|%s-->\n"%(self.name,self.guid)
        out+="\n"
        out+=str(MDHeader(2,"%s"%self.name))
        out+="\n"
        out+=str(MDCode(self.datahr,"yaml"))
        out+="\n"
        return out

    __str__=__repr__

class MarkdownDocument():

    def __init__(self,content="",path=""):

        if path!="":
            content=j.sal.fs.fileGetContents(path)

        self._content=content
        self._tokens=""
        self._changed_tokens=False
        self.items=[]
        self._parse()
        self._dataCache={}


    def _findFancyHeaders(self):

        out=[]
        for line in self.content.split("\n"):
            if line.startswith("===="):
                out[-1]="# %s"%out[-1]
                continue

            if line.startswith("-----"):
                out[-1]="## %s"%out[-1]
                continue
            out.append(line)

        self._content = "\n".join(out)

    def addMDTable(self):
        """
        returns table which needs to be manipulated
        """
        t=MDTable()
        self.items.append(t)
        return t

    def addMDHeader(self,level,title):
        """
        """
        self.items.append(MDHeader(level,title))

    def addMDListItem(self,level,text):
        """
        """
        self.items.append(MDListItem(level,text))

    def addMDComment(self,text):
        """
        """
        self.items.append(MDComment(text))

    def addMDComment1Line(self,text):
        """
        """
        self.items.append(MDComment1Line(text))

    def addMDBlock(self,text):
        """
        """
        self.items.append(MDBlock(text))

    def addMDCode(self,text,lang):
        """
        """
        self.items.append(MDCode(text,lang))

    def addMDData(self,ddict,name="",guid=""):
        ddict=copy.copy(ddict)
        self.items.append(MDData(ddict,name,guid))

    def _parse(self):
        self._findFancyHeaders()
        state=""
        block=""
        prevListLevel=0
        curListLevel=1
        substate=""

        def addBlock(block):
            if block.strip()!="":
                self.items.append(MDBlock(block))
            substate=""
            state=""
            return ""

        for line in self.content.split("\n"):

            #HEADERS
            if line.startswith("#"):
                block=addBlock(block)
                level=0
                line0=line
                while line0.startswith("#"):
                    level+=1
                    line0=line0[1:]
                title=line0.strip()
                self.items.append(MDHeader(level,title))
                continue

            linestripped=line.strip()

            #substate
            if linestripped.startswith("<!--") and linestripped.endswith("-->"):
                substate=linestripped[4:-3].strip()
                self.addMDComment1Line(substate)
                block=""
                state=""
                continue

            if line.startswith("<!-"):
                state="COMMENT"
                continue


            #process all comment states
            if state.startswith("COMMENT"):
                if line.startswith("-->"):
                    state=""
                    if state=="COMMENT":
                        self.items.append(MDComment(block))
                    block=""
                    continue
                block+="%s\n"%line

            #LIST
            if linestripped.startswith("-") or linestripped.startswith("*"):
                if state=="" :
                    block=addBlock(block)
                    state="LIST"
                    curListLevel=1
                    prevListLevel=0
                    prevlevels={0:1}

                if state=="LIST":
                    if not (linestripped.startswith("-") or linestripped.startswith("*")):
                        state
                    line0=line
                    level=0
                    while line0.startswith(" "):
                        level+=1
                        line0=line0[1:]
                    #see how level goes up or down
                    if level in prevlevels:
                        curListLevel=prevlevels[level]
                    elif level>prevListLevel:
                        curListLevel+=1
                        prevlevels[level]=curListLevel
                    prevListLevel=level
                    self.items.append(MDListItem(curListLevel,line.strip("* ")))
                    continue
            else:
                #get out of state state
                if state=="LIST":
                    state=""

            if state=="TABLE" and not linestripped.startswith("|"):
                state=""
                self.items.append(table)
                table=None
                cols=[]

            #TABLE
            if state!="TABLE" and linestripped.startswith("|"):
                state="TABLE"
                block=addBlock(block)
                cols=[item.strip() for item in line.split("|") if item.strip()!=""]
                table=MDTable()
                table.addHeader(cols)
                continue

            if state=="TABLE":
                if linestripped.startswith("|") and linestripped.endswith("|") and line.find("---")!=-1:
                    continue
                cols=[item.strip() for item in line.split("|") if item.strip()!=""]
                table.addRow(cols)
                continue

            #CODE
            if state=="" and linestripped.startswith("```") or linestripped.startswith("'''"):
                block=addBlock(block)
                state="CODE"
                lang=line.strip("'` ")
                continue

            if state=="CODE":
                if linestripped.startswith("```") or linestripped.startswith("'''"):
                    state=""
                    # from pudb import set_trace; set_trace()
                    if substate.startswith("data"):
                        tmp,name,guid=substate.split("|")
                        data=j.data.serializer.yaml.loads(str(block))
                        self.addMDData(data,name,guid)
                    else:
                        self.items.append(MDCode(block,lang))
                    block=""
                else:
                    block+="%s\n"%line
                continue

            if linestripped!="":
                block+="%s\n"%line
            else:
                block=addBlock(block)

    @property
    def content(self):
        return self._content

    @property
    def tokens(self):
        if  self._tokens=="":
            bl=BlockLexer()
            self._tokens=bl.parse(self._content)
        return self._tokens

    @tokens.setter
    def tokens(self,val):
        self._changed_tokens=True
        self._tokens=val


    def getHashList(self,ttype):
        res={}
        for item in self.items:
            if item.type=="data" and item.name==ttype:
                res[item.guid]=item.hash
        return res

    def getDataCollection(self,ttype):
        res={}
        for item in self.items:
            if item.type=="data" and item.name==ttype:
                res[item.guid]=item.ddict
                key="%s__%s"%(ttype,item.guid)
                self._dataCache[key]=item
        return res

    def getDataObj(self,ttype,guid):
        key="%s__%s"%(ttype,guid)
        if key not in self._dataCache:
            self.getDataCollection()
        if key not in self._dataCache:
            raise j.exceptions.Input("Cannot find object with type:%s guid:%s"%(ttype,guid))
        return self._dataCache[key].ddict


    def __repr__(self):
        out=""
        prevtype=""
        for item in self.items:
            if item.type not in ["list"]:
                if prevtype=="list":
                    out+="\n"
                out+=str(item).strip()+"\n\n"
            else:
                out+=str(item).rstrip()+"\n"

            prevtype=item.type
        return out

    __str__=__repr__



# md=MarkdownDocument(example)

# test={}
# test["descr"]="""
# Tables

# Tables aren't part of the core Markdown spec, but they are part of GFM and Markdown Here supports them. They are an easy way of adding tables to your email -- a task that would otherwise require copy-pasting from another application.

# Colons can be used to align columns.

# """
# test["nr"]=3
# test["subd"]={"nr2":3,"item":"sss"}

# md.addMDData(test,"test","myguid")

# test["nr"]=4
# md.addMDData(test,"test","myguid2")

# md2=MarkdownDocument(str(md))

# print (md2.getHashList("test"))

class MarkdownFactory:
    def __init__(self):
        self.__jslocation__="j.data.markdown"

    def getDocument(self,content="",path=""):
        """
        returns a tool which allows easy creation of a markdown document
        """
        return MarkdownDocument(content,path)
