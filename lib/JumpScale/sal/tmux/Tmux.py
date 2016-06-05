from JumpScale import j

import tmuxp

class Session:
    def __init__(self,session):

        self.id=session.get("session_id")
        self.name=session.get("session_name")
        self.mgmt=session
        self.reload()

    def reload(self):
        self.windows=[]
        for w in self.mgmt.list_windows():
            self.windows.append(Window(self,w))

    def delWindow(self,name):
        windows=self.mgmt.list_windows()
        if len(windows)<2:
            self.getWindow(name="ignore",removeIgnore=False)
        for w in self.mgmt.windows:
            wname=w.get("window_name")
            if name ==wname:
                w.kill_window()
        self.reload()

    def existsWindow(self,name):
        for window in self.windows:
            if window.name==name:
                return True
        return False

    def getWindow(self,name,start_directory=None,attach=False,reset=False,removeIgnore=True):

        # from pudb import set_trace; set_trace()
        if reset:
            self.delWindow(name)

        for window in self.windows:
            if window.name==name:
                if self.existsWindow("ignore") and removeIgnore:
                    self.delWindow("ignore")
                return self.windows[name]

        print ("create window:%s"%name)

        res=self.mgmt.new_window(name,start_directory=start_directory,attach=attach)

        window=Window(self,res)
        self.windows.append(window)
        window.select()

        #when only 1 pane then ignore had to be created again
        if self.existsWindow("ignore") and removeIgnore:
            self.delWindow("ignore")

        return window


    def kill(self):
        raise j.exceptions.RuntimeError("kill")

    def __repr__(self):
        return ("session:%s:%s"%(self.id,self.name))

    __str__=__repr__

class Window:
    def __init__(self,session,window):
        self.name=window.get("window_name")
        self.session=session
        self.mgmt=window
        self.id=window.get("window_id")
        self._reload()

    def _reload(self):
        if len(self.mgmt.panes)==1:
            self.panes=[Pane(self,self.mgmt.panes[0])]
        else:
            self.panes=[]
            for pane in self.mgmt.panes:
                self.panes.append(Pane(self,pane))

    def existsPane(self,name="",id=0):
        """
       if there is only 1 and name is not same then name will be set
        """
        for pane in self.panes:
            if pane.name==name:
                return True
            if pane.id==id:
                return True
        return False


    def getPane(self,name,killothers=False):
        """
       if there is only 1 and name is not same then name will be set
        """
        if len(self.panes)==1:
            self.panes[0].name=name
            return self.panes[0]
        for pane in self.panes:
            if pane.name==name:
                if killothers:
                    for pane2 in self.panes:
                        if pane2.name!=name:
                            pane2.kill()
                return pane
        raise j.exceptions.RuntimeError("Could not find pane:%s.%s"%(self.name,name))


    def select(self):
        self.mgmt.select_window()

    def kill(self):
        # from pudb import set_trace; set_trace()
        if len(self.session.windows.keys())<2:
            self.session.getWindow(name="ignore")
        print ("KILL %s"%self.name)
        self.mgmt.kill_window()

    def __repr__(self):
        return ("window:%s:%s"%(self.id,self.name))

    __str__=__repr__

class Pane:

    def __init__(self,window,pane):
        self.mgmt=pane
        self.id=pane.get("pane_id")
        self.name=pane.get("pane_title")
        self.window=window

    def select(self):
        self.mgmt.select_pane()

    def _split(self,name,ext="-v"):
        self.select()
        j.sal.tmux.execute("split-window %s"%ext)
        #look for pane who is not found yet
        panefound=None
        for pane2 in self.window.mgmt.panes:
            if not self.window.existsPane(id=pane2.get("pane_id")):
                if panefound!=None:
                    raise j.exceptions.RuntimeError("can only find 1 pane, bug")
                panefound=pane2
        pane=Pane(self.window,panefound)
        pane.name=name
        self.window.panes.append(pane)
        return pane

    def splitVertical(self,name):
        return self._split(name,"-v")

    def splitHorizontal(self,name):
        return  self._split(name,"-h")

    def __repr__(self):
        return ("panel:%s:%s"%(self.id,self.name))

    __str__=__repr__

class Tmux:

    def __init__(self):
        self.__jslocation__ = "j.sal.tmux"
        self.sessions={}

    def _getServer(self,name,firstWindow=""):
        try:
            s=tmuxp.Server()
            s.list_sessions()
        except Exception as e:
            if firstWindow=="":
                j.tools.cuisine.local.tmux.createSession(name,["ignore"])
            else:
                j.tools.cuisine.local.tmux.createSession(name,[firstWindow])
            s=tmuxp.Server()
            s.list_sessions()
        return s


    def getSession(self,name,reset=False, attach=False,firstWindow=""):
        if reset and name in self.sessions:
            self.sessions[name].kill()

        if name in self.sessions:
            return self.sessions[name]

        print ("create session:%s"%name)


        s=self._getServer(name,firstWindow=firstWindow)

        if reset:
            res=s.new_session(session_name=name, kill_session=kill_session, attach=attach)
        else:
            res=None
            for se in s.list_sessions():
                sname=se.get("session_name")
                if name ==sname:
                    res=se
            if res==None:
                res=s.new_session(session_name=name, kill_session=False, attach=attach)

        self.sessions[name]=Session(res)
        return self.sessions[name]

    def execute(self,cmd):
        cmd="tmux %s"%cmd
        j.do.execute(cmd,showout=False)

    def createPanes4Actions(self,sessionName="main",windowName="actions",reset=True):
        session=self.getSession(sessionName,firstWindow="main")
        window=session.getWindow(windowName,reset=reset)

        main=window.getPane(name="main",killothers=True)

        out=main.splitVertical("out")
        cmds=out.splitVertical("cmds")

        o3=cmds.splitHorizontal("o3")
        o1=cmds
        o1.name="o1"

        o2=o1.splitHorizontal("o2")
        o4=o3.splitHorizontal("o4")
        j.application.break_into_jshell("DEBUG NOW oioioi")
