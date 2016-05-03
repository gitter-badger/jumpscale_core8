import os
import sys
from datetime import date

from JumpScale import j

from EasyDialogGeneric import EasyDialogGeneric

class EasyDialogConsole(EasyDialogGeneric):

    _NAVIGATION_CONTROL_FLAGS = ['n', 'next', 'p', 'previous']
    def askFilePath(self, message, startPath = None):
        """
        Prompts for a selection of a file path starting from startPath if given and '/' if not

        @param message: message that would be displayed to the user above the selection menu
        @param startPath: base dir of the navigation tree
        @return: path to the file selected
        """

        filepath=""
        currentDir = startPath or "/"
        if j.sal.fs.isEmptyDir(currentDir):
            raise j.exceptions.RuntimeError('Startpath directory contains no files, please enter a non empty dir')
        while(j.sal.fs.isDir(currentDir)):
            dirs = j.sal.fs.walk(currentDir, return_folders = 1)
            if dirs:
                previousDir = currentDir
                currentDir = self.askChoice(message, dirs)
            else:
                j.tools.console.echo('This directory contains no files, please choose a different one')
                currentDir = previousDir

        filepath = currentDir
        return filepath


    def askDirPath(self, message, startPath = None):
        """
        Prompts for a selection of a file path starting from startPath if given and '/' if not

        @param message: message that would be displayed to the user above the selection menu
        @param startPath: base dir of the navigation tree
        @return: path to the directory selected
        """

        currentDir = startPath or "/"
        traverse = True
        while(j.sal.fs.isDir(currentDir) and traverse and not j.sal.fs.isEmptyDir(currentDir)):
            dirs = j.sal.fs.walk(currentDir, return_folders = 1, return_files = 0)
            currentDir = self.askChoice(message, dirs)
            traverse = not self.askYesNo("To Choose Current folder [y/yes] to continue navigation [n/No]?", 'y')
        return currentDir

    def askString(self, question, defaultValue = None, validator=None):
        """
        Asks the user the supplied question and prompt for an answer, if none given the default value is used
        @param question: question to be displayed
        @param defaultValue: if the user did not provide a response this value is used as an answer
        @param validator: regex validation value
        @return: response string or the default value
        """
        return j.tools.console.askString(question, defaultValue if defaultValue else '', validator)

    def askInt(self, question, defaultValue = None):
        """
        Asks user the supplied question and prompt for an answer, if none given the default value is used, the response and the default value must be valid integer

        @param question: question to be displayed
        @param defaultValue: if the user did not provide a response this value is used as an answer
        @return: response integer or the default value
        """

        return self.askInteger(question, defaultValue)


    def askYesNo(self, question, defaultValue = None):
        """
        Asks user the supplied question and prompt for an answer, if none given the default value is used, the response and the default value one of the values [y|Y|yes|Yes..n|N|No..]

        Currently the default value effect is ignored since it would require changing the jumpscale vapp
        @param question: question to be prompted
        @param defaultValue: if the user did not provide a response this value is used as an answer
        @return: response answer or the default value
        """
        return j.tools.console.askYesNo(question)

    def askPassword(self, question, confirm=True, regex=None, retry=-1, defaultValue=None):
        """
        Asks the supplied question and prompts for password

        @param question: question to be displayed
        @return: response string
        """
        if defaultValue:
            question = question.rstrip(': ')

            question = '%s [%s]: ' % (question, '*' * len(defaultValue))

        value = j.tools.console.askPassword(question, confirm, regex, retry)

        if defaultValue and not value:
            value = defaultValue

        return value

    def message(self,message):
        """
        prints the given message to the screen

        @param message: message to print
        """
        j.tools.console.echo(message)

    def askInteger(self, question, defaultValue = None):
        """
        Asks user the supplied question and prompt for an answer, if none given the default value is used, the response and the default value must be valid integer

        @param question: question to be displayed
        @param defaultValue: if the user did not provide a response this value is used as an answer
        @return: response integer or the default value
        """
        return j.tools.console.askInteger(question, defaultValue)


    def askChoice(self, question, choices, defaultValue = None, pageSize = 40, sortChoices=False, sortCallBack=None):
        """
        Ask the user the supplied question and list the choices to choose from, if no response given the default value is used

        @param question: question to be display to the user
        @param choices: list of choinavigateToces for the user to choose from
        @param defaultValue: the value that will be used if no response given
        @param pageSize: max number of choices that can be prompted to the user in a single screen
        @param sortChoices: if True, choices will be sorted before showing them to the user
        @param sortCallBack: A callback function to handle the sorting of the choices (will only be used if sortChoices is set to True)

        @return:  selected choice
        """

        if j.application.interactive!=True:
            raise j.exceptions.RuntimeError("Cannot ask a choice in an list of items in a non interactive mode.")

        defaultValues = list()

        if defaultValue:
            defaultValues = [value.strip() for value in defaultValue.split(',')]
            #we choose tolerant approach by just filtering out the invalid defaultValues entries, without raising an error
            defaultValues = [value for value in defaultValues if value in choices]

        result = None

        if sortChoices:
            if not sortCallBack:
                choices.sort()
            else:
                sortCallBack(choices)

        if len(choices) > pageSize and not j.core.platformtype.myplatform.isLinux():
            #@todo implement, make multi screen, sort & allow default value usage, use next-previous (also n&p as short notation)
            ##result = self._handleScreens(choices, defaultValues, pageSize = pageSize)[0]
            j.tools.console.echo("Too many potential choices, more than %s, choose again" % pageSize)
            return False
        else:
            result=j.tools.console.askChoice(choices, question)
        return result



    def askChoiceMultiple(self, question, choices, defaultValue = None, pageSize = 40, sortChoices=False, sortCallBack=None):
        """
        Ask the user the supplied question and list the choices to choose from, if no response given the default value[s] is used

        @param question: question to be display to the user
        @param choices: list of choices for the user to choose from
        @param defaultValue: default value assumed if no user response is given, default value can be a single value or a comma separated list of values
        @param pageSize: max number of choices that can be prompted to the user in a single screen
        @param sortChoices: if True, choices will be sorted before showing them to the user
        @param sortCallBack: A callback function to handle the sorting of the choices (will only be used if sortChoices is set to True)

        @return:  selected choice[s] or default value[s]
        """

        if j.application.interactive!=True:
            raise j.exceptions.RuntimeError("Cannot ask a choice in a list of items in a non interactive mode.")

        defaultValues = list()
        defaultValue=str(defaultValue)
        if defaultValue:
            if defaultValue.find(",")==-1:
                defaultValues=[defaultValue]
            else:
                defaultValues = [value.strip() for value in defaultValue.split(',')]
                #we choose tolerant approach by just filtering out the invalid defaultValues entries, without raising an error
                defaultValues = [value for value in defaultValues if value in choices]


        result = None

        if sortChoices:
            if not sortCallBack:
                choices.sort()
            else:
                sortCallBack(choices)

        if len(choices) > pageSize:
            j.tools.console.echo("Too many potential choices, more than %s, choose again" % pageSize)
            return False
            ##j.tools.console.echo("%s\n"%question)
            ##@todo implement, make multi screen, sort & allow default value usage, use next-previous (also n&p as short notation)
            ##result = self._handleScreens(choices, defaultValues, pageSize = pageSize, multiSelection = True)
        else:
            result=j.tools.console.askChoiceMultiple(choices,question)

        return result



    def _handleScreens(self, choices, defaultValue, pageSize=40, multiSelection=False):
        """
        Handles multi-screen selections

        @param choices: choices to choose from
        @param defaultValue: default value if not response is supplied
        @param pageSize: max number of choices that can be prompted to the user in a single screen
        @param multiSelection: whether the more than one selection is allowed or not
        """
        raise j.exceptions.RuntimeError("IMPLEMENTATION of handlescreens is too bad, no try except allowed, will stop now")
    #@todo reimplement (NO TRY EXCEPT, USE Q.CONSOLE classes much more) (kds: tried to get it to work but code is just not good enough)

        def ask(choices, pageSize, currentLocation, defaultValue, multiSelection):
            #self._showPage(choices, pageSize, currentLocation, defaultValue, multiSelection, False)
            try:
                return self._showPage(choices, pageSize, currentLocation, defaultValue, multiSelection, False)
            except :
                logger = j.logger.get('EasyDialogConsole')
                logger.error_tb()
                return ask(choices, pageSize, currentLocation, defaultValue, multiSelection)

        currentLocation = 0
        selection = ask(choices, pageSize, currentLocation, defaultValue, multiSelection)
        currentLocation += pageSize
        while selection[0] in EasyDialogConsole._NAVIGATION_CONTROL_FLAGS:
            if selection[0] == 'n' or selection[0] == 'next':
                selection = ask(choices, pageSize, currentLocation, defaultValue, multiSelection)
                currentLocation += pageSize
            elif selection[0] == 'p' or selection[0] == 'previous':
                currentLocation -= pageSize
                if currentLocation<0:
                    currentLocation=0
                ask(choices, pageSize, currentLocation, defaultValue, multiSelection)

        return [choices[int(element) - 1] for element in selection]


    def _showPage(self, choices, pageSize, currentLocation, defaultValue, multiSelection, up):
        """
        Show next/previous page of choices

        @param choices: choices to choose from
        @param pageSize: max number of choices that can be prompted to the user in a single screen
        @param currentLocation: the current location of the cursor
        @param multiSelection: whether the more than one selection is allowed or not
        @param up: whether to show the next page or previous one
        """
        raise j.exceptions.RuntimeError("IMPLEMENTATION of handlescreens is too bad, no try except allowed, will stop now")
        if up:
            numberOfChoices = len(choices)
            if currentLocation > numberOfChoices:
                j.logger.log('Location [%s] exceeds the limits [%s]'%(currentLocation, numberOfChoices))
                raise ValueError('Last page reached')

            messageHeader = 'Make a selection. '
            if currentLocation == 0:
                messageBody = "Use (n) to show next set of choices"
            elif currentLocation + pageSize >= numberOfChoices:
                messageBody = "Use (p) to show previous set of choices"
            else:
                messageBody = "Use (n/p) to show next/previous set of choices"
            j.tools.console.echo("%s%s"%(messageHeader, messageBody))
            currentPage = choices[currentLocation: currentLocation + pageSize]
            index = currentLocation
        else:
            if currentLocation < 0:
                j.logger.log('Location [%s] cannot be less than zero'%currentLocation)
                raise ValueError('First page reached')
            messageHeader = 'Make a selection. '
            if currentLocation - pageSize <= 0:
                messageBody = "Use (n) to show next set of choices"
            else:
                messageBody = "Use (n/p) to show next/previous set of choices"
            j.tools.console.echo("%s%s"%(messageHeader, messageBody))
            currentPage = choices[currentLocation - pageSize: currentLocation]
            index = currentLocation - pageSize
        for choise in currentPage:
            index += 1
            j.tools.console.echo("   %s: %s" % (index, choise))
        j.tools.console.echo("")
        selection = j.tools.console.askString("   Select Nr,%s %s"%('use comma separation if more e.g. "1,4"' if multiSelection else '',messageBody))

        #selection OR default
        if selection:
            selection = self._checkSelection(selection, choices, multiSelection)
        elif defaultValue:
            selection = [choices.index(value) + 1 for value in defaultValue] #convert values to corresponding indexes
        else:
            raise ValueError("No/Invalid default value provided, please try again and select Nr.")
        return selection


    def askMultiline(self, question):
        """
        Asks the user the supplied question, where the answer could be multi-lines

        @param question: the question to be displayed
        """
        return j.tools.console.askMultiline(question)

    def askDate(self, question, minValue=None, maxValue=None, selectedValue=None, format='%Y/%m/%d'):
        """
        Asks user the supplied question, a valid answer is a date between minValue and maxValue

        Currently in the EasyDialogConsole implementation ignores the format parameter and  only dates with format YYYY/MM/DD are supported

        @param question: question that will be prompted to the user
        @param minValue: optional value for the lower boundary date
        @param maxValue: optional value for the upper boundary date
        @param selectedValue:
        @param  format: the format of the input date
        """

        format = '%Y/%m/%d'
        #@todo implement is simple input, show format [day]/[month]/[year]  year is 09 or 2009, day is 2 or 02
        j.tools.console.echo("%s\n"%question)
        j.tools.console.echo("Enter a date with format YYYY/MM/DD, where year can be 09 or 2009, day is 2 or 02:")
        userInput = eval(input())
        #@todo validate date is in correct format
        yearPrefix = "20"
        if minValue:
            minValueDate = minValue.split('/')
            if len(minValueDate[0]) == 2:
                minValueDate[0] = "%s%s"%(yearPrefix, minValueDate[0])
            minValue = date(int(minValueDate[0]),int(minValueDate[1]), int(minValueDate[2]))
        if maxValue:
            maxValueDate = maxValue.split('/')
            if len(maxValueDate[0]) == 2:
                maxValueDate[0] = "%s%s"%(yearPrefix, maxValueDate[0])
            maxValue = date(int(maxValueDate[0]),int(maxValueDate[1]), int(maxValueDate[2]))

        dateValues = userInput.split('/')
        if len(dateValues[0]) == 2:
            dateValues[0] = "%s%s"%(yearPrefix, dateValues[0])
        selectedDate =  date(int(dateValues[0]),int(dateValues[1]), int(dateValues[2]))

        if minValue and self._compareDates(minValue, selectedDate) > 0:
            raise AttributeError("Provided date [%s] must be greater than min date [%s]"%(selectedDate, minValue))
        if maxValue and self._compareDates(selectedDate, maxValue) > 0 :
            raise AttributeError("Provided date [%s] must be less than max date [%s]"%(selectedDate, maxValue))
        return selectedDate.strftime(format)


    def showProgress(self, minvalue, maxvalue, currentvalue):
        """
        Shows a progress bar according to the given values

        @param minvalue: minVlue of scale
        @param maxvalue: maxvlaue of scale
        @param currentvalue: the current value to show the progress
        """

        if currentvalue < minvalue or currentvalue > maxvalue:
            raise AttributeError("Provided value [%s] must be between [%s] and [%s]"%(currentvalue, minvalue, maxvalue))
        if maxvalue < minvalue:
            raise AttributeError("minvalue [%s] cannot be larger than maxvalue [%s]"%(minvalue, maxvalue))
        scale = maxvalue - minvalue
        progressValue = ((currentvalue - minvalue) * 100) / scale
        textProgressScal = 50
        index = 0
        progressBar = '['
        while index < int(progressValue / int(100/textProgressScal)):
            progressBar = "%s#"%progressBar
            index += 1
        progressBar = "%s%s] %s%%"%(progressBar, ' '*(textProgressScal + 1 - len(progressBar)), progressValue)

        return progressBar

    def showLogging(self, text):
        """
        Shows logging message
        """
        j.tools.console.echo(text, 1)


    def navigateTo(self, url):
        raise NotImplementedError('Not implemented yet')


    def askIntegers(self, question):
        """
        Asks user the supplied question and prompt for an answer

        @param question: question to be prompted
        @return: response integer
        """

        raise NotImplementedError('Not implemented yet')

    def _checkSelection(self, selection, choices, multiSelection):
        """
        checks if a selection is a valid selection or not

        @param selection: unprocessed user selection, i.e. single value or comma separated list, or control characters: p|n|previous|next
        @param choices: choices to choose from
        @param multiSelection: whether the more than one selection is allowed or not
        """
        raise j.exceptions.RuntimeError("IMPLEMENTATION of handlescreens is too bad, no try except allowed, will stop now")
        selections = [value.strip() for value in selection.split(',')]
        if not multiSelection:
            selections = selections[:1]

        if selections[0] in EasyDialogConsole._NAVIGATION_CONTROL_FLAGS:
            selections = selections[:1] #ignore the rest of the values, if any
        else:
            try:
                selections = list(map(int, selections)) #convert to int
            except ValueError as ex:
                raise ValueError('Invalid numeric values [%s]'%selections)

            if max(selections) > len(choices) or min(selections) <= 0:
                raise ValueError('Selection out of range')


        return selections

    def chooseDialogType(self,type):
        """
        supported types today: console,win32,wizardserver
        @param type DialogType enumerator
        """
        raise NotImplementedError('Not implemented yet')

    def clear(self):
        """
        Clears the screen/form.
        """
        if os.name == "posix":
            # Unix/Linux/MacOS/BSD/etc
            os.system('clear')
        elif os.name in ("nt", "dos", "ce"):
            # DOS/Windows
            os.system('CLS')


    def _compareDates(self, firstDate, secondDate):
        """
        Compares tow dates

        @param firstDate:
        @param secondDate:
        @return: positive integer if first date is greater than second date, 0 if equals, and negative integer if less than
        """
        j.logger.log("trying to compare [%s] with [%s]"%(firstDate, secondDate), 3)
        daysDifference = firstDate - secondDate
        return daysDifference.days
