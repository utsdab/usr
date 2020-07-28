import re
import os

from zoo.libs.utils import filesystem
from zoo.libs.utils import general


class NameManager(object):
    """The name manager deals with the maniplation of a string based on an expression allowing for a formalised
    naming convention, we use the terms 'rule' and 'tokens' throughout the class to describe the logic.
    rules are just a basic expression like so '{side}_{area}_{counter}_{type}', the '_' isnt not necessary for any logic.
    the characters within the curly brackets are tokens which will be replace when its resolved.
    tokens have a set of possible values that it can use if the value set this token to doesn't exist then it wont be
    resolved. you can add tokens and values in memory per instance or you can add it to the config JSON file.
    """
    refilter = r"(?<={)[^}]*"
    counter = {"value": 0, "padding": 3, "default": 0}

    def __init__(self, activeRule=None, configPaths=None):
        """
        :param activeRule: the active rule to set, see setActiveRule()
        :type activeRule: str
        """
        self._activeRule = None
        self.config = None
        self.configPaths = configPaths
        if configPaths:
            self.load(configPaths)
        if activeRule:
            self.setActiveRule(activeRule)
        self.config["tokens"]["counter"] = self.counter

    def setActiveRule(self, rule):
        """Sets the active rule, rules a basic expression that dictate how a name is resolved
        :param rule: the rule name, see method rules()
        :type rule: str
        """
        self._activeRule = rule

    def activeRule(self):
        """Returns the currently active rule name
        :rtype: str
        """
        return self._activeRule

    def rules(self):
        """returns all the currently active rules
        :return: a list of active rule names
        :rtype: list
        """
        return self.config["rules"].keys()

    def getExpression(self, rule):
        rule = self.config["rules"].get(rule)
        if rule:
            return rule["expression"]

    def ruleFromExpression(self, expression):
        for i, data in self.config["rules"].items():
            if data["expression"] == expression:
                return i

    def expression(self):
        return self.config["rules"][self.activeRule()]["expression"]

    def setExpression(self, value):
        self.config["rules"][self.activeRule()]["expression"] = value

    def expressionList(self):
        return [i["expression"] for i in self.config["rules"].values()]

    def description(self):
        return self.config["rules"][self.activeRule()]["description"]

    def setRuleDescription(self, value):
        self.config["rule"][self.activeRule()]["description"] = value

    def creator(self):
        return self.config[self.activeRule()]["creator"]

    def setCreator(self, creator):
        self.config[self.activeRule()]["creator"] = creator

    def addToken(self, name, value, default):
        data = {"default": default}
        data.update(value)
        self.config["tokens"][name] = data

    def hasToken(self, tokenName):
        return tokenName in self.config["tokens"]

    def hasTokenValue(self, tokenName, value):
        return self.hasToken(tokenName) and value in self.config["tokens"][tokenName]

    def updateTokenValue(self, name, value):
        if not self.hasToken(name):
            raise ValueError("Config has no token called {}".format(name))
        self.config["tokens"][name].update(value)

    def tokenValue(self, name):
        if not self.hasToken(name):
            raise ValueError("Config has no token called {}".format(name))
        # @todo need to update this push it into the config
        if name == "counter":
            return self.config["tokens"][name]["value"]
        return self.config["tokens"][name]["default"]

    def tokenValues(self, token):
        ret = self.config["tokens"][token].copy()

        if token == "counter":
            del ret['value']

        del ret['default']
        return ret.keys()

    def addRule(self, name, expression, description, asActive=True):
        self.config["rule"].update({name: {"expression": expression,
                                           "description": description}})
        if asActive:
            self.setActiveRule(name)

    def rule(self, name):
        if self.config:
            return self.config["rule"].get(name)

    def setTokenDefault(self, name, value):
        tokens = self.config["tokens"]
        if name in tokens:
            tokens[name]["default"] = tokens[name].get(value, value)

    def overrideToken(self, name, value, **kwargs):
        if not self.hasToken(name):
            self.addToken(name, {value, value}, default=value)

        if name == "counter":
            configData = self.config["tokens"][name]
            self.config["tokens"][name]["padding"] = {"value": value,
                                                      "padding": kwargs.get("padding", configData["padding"]),
                                                      "default": kwargs.get("default", configData["default"])}
            return

        tokens = self.config["tokens"]
        tokens[name]["default"] = value
        tokens[name].update(kwargs)

    def expressionFromString(self, name):
        """Returns the expression from the name, if the name cannot be resolved then we raise ValueError,
        If we resolve to multiple expressions then we raise ValueError. Only one expression is possible.
        To resolve a name, all tokens must exist within the config and we must be able to resolve more
        than 50% for an expression for it to be viable.
        
        :param name: the string the resolve
        :type name: str
        :return: the config expression eg. {side}_{type}{section}
        :rtype: str
        """
        tokens = self.config["tokens"]
        expressedname = []
        for tname, tokenValues in tokens.items():
            if tname == "counter":
                continue
            for tokenName, tkValue in tokenValues.items():
                if tname not in expressedname and tkValue in name:
                    expressedname.append(tname)
                    break

        # we dont have an exact match so lets find which expression is the most probable
        possibles = set()
        tokenisedLength = len(expressedname)
        for expression in self.expressionList():
            expressionTokens = re.findall(NameManager.refilter, expression)
            totalcount = 0
            for tokname in expressedname:
                if tokname in expressionTokens:
                    totalcount += 1
            if totalcount > tokenisedLength / 2:
                possibles.add((expression, totalcount))
        if not possibles:
            raise ValueError("Could not resolve name: {} to an existing expression".format(name))

        maxPossible = max([i[1] for i in possibles])
        truePossibles = []
        # filter out the possibles down to just the best resolved
        for possible, tc in iter(possibles):
            if tc == maxPossible:
                truePossibles.append(possible)
        if len(truePossibles) > 1:
            raise ValueError("Could not Resolve name: {}, due to to many possible expressions".format(name))
        return truePossibles[0]

    def resolve(self):
        expression = self.expression()
        tokens = re.findall(NameManager.refilter, expression)
        newStr = expression
        for token in tokens:
            if token == "counter":
                val = str(self.counter["value"]).zfill(self.counter["padding"])
            else:
                val = self.config["tokens"][token]["default"]
            newStr = re.sub("{" + token + "}", val or "null", newStr)
        return newStr

    def save(self, configPath):
        filesystem.saveJson(self.config, configPath)
        return configPath

    def refresh(self):
        self.config = {}
        self.load(self.configPaths)

    def load(self, configPaths):
        data = {}
        self.configPaths = configPaths
        for config in configPaths:
            if not os.path.exists(config) or not config.endswith(".json"):
                continue
            userData = filesystem.loadJson(config)
            general.merge(data, userData)
            rules = userData.get("rules")
            tokens = userData.get("tokens")
            if rules:
                data["rules"].update(rules)
            if tokens:
                data["tokens"].update(tokens)
        self.config = data
