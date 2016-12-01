#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################

import indigo
import random
import logging
import numpy as np
import time


class Plugin(indigo.PluginBase):
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        super(Plugin, self).__init__(pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
        self.logger.setLevel(logging.INFO)

    def startup(self):
        self.setLogLevel()
        self.logger.debug(u"startup called")
        self.parentDevIdsWeUseDict = []
        indigo.devices.subscribeToChanges()

    def shutdown(self):
        self.logger.debug(u"shutdown called")

    def _refreshState(self, dev, logRefresh=False):
        # TODO: Fix error handling if parentDevice don't exits
        parentDevice = indigo.devices[int(dev.ownerProps[u"parentDeviceId"])]
        ts = time.time()
        keyValueList = []
        if "curEnergyLevel" in dev.states:
            if parentDevice.states['onOffState']:
                if u"brightnessLevel" in parentDevice.states:
                    watts = self.getCurPower(dev, int(parentDevice.states.get("brightnessLevel")))
                else:
                    watts = float(dev.ownerProps[u"powerAtOn"])
                wattsStr = "%.2f W" % (watts)
                accumEnergyTotalTS = dev.states.get("accumEnergyTotalTS", ts)
                if accumEnergyTotalTS == 0:
                    accumEnergyTotalTS = ts
                energy = ((ts - accumEnergyTotalTS) / 3600 * watts) / 1000
                self._addAccumEnergy(dev, energy, ts)
            else:
                watts = 0.0
                wattsStr = "%d W" % (watts)
                self._addAccumEnergy(dev, 0, ts)
            keyValueList.append(
                {'key': 'curEnergyLevel', 'value': watts, 'uiValue': wattsStr})

        dev.updateStatesOnServer(keyValueList)

    def _addAccumEnergy(self, dev, energy, ts):
        keyValueList = []
        if "accumEnergyTotal" in dev.states:
            accumKwh = dev.states.get("accumEnergyTotal", 0) + energy
            accumKwhStr = "%.3f kWh" % (accumKwh)
            keyValueList.append(
                {'key': 'accumEnergyTotal', 'value': accumKwh, 'uiValue': accumKwhStr})
            keyValueList.append(
                {'key': 'accumEnergyTotalTS', 'value': ts, 'uiValue': "%d" % ts})
            dev.updateStatesOnServer(keyValueList)

    def runConcurrentThread(self):
        try:
            while True:
                for dev in indigo.devices.iter("self"):
                    if not dev.enabled or not dev.configured:
                        continue
                    self._refreshState(dev)
                self.sleep(60)
        except self.StopThread:
            pass  # Optionally catch the StopThread exception and do any needed cleanup.

    ########################################
    # Device Creation Callbacks
    ######################
    def getDeviceList(self, filter="supportsOnState", valuesDict=None, typeId="", targetId=0):
        # A little bit of Python list comprehension magic here. Basically, it iterates through
        # the device list and only adds the device if it has the filter property and is enabled.
        return [(dev.id, dev.name) for dev in indigo.devices if hasattr(dev, filter)]

    def devicesThatSupportOnState(self, filter="", valuesDict=None, typeId="", targetId=0):
        menuItems = []
        for dev in indigo.devices.iter("indigo.relay, indigo.dimmer"):
            menuItems.append((dev.id, dev.name))
        for dev in indigo.devices.iter("indigo.sensor, props.SupportsOnState"):
            menuItems.append((dev.id, dev.name))
        return menuItems

    def parentDeviceIdChanged(self, valuesDict, typeId, devId):
        if typeId == u"virtualDeviceEnergyMeter":
            dev = indigo.devices[int(valuesDict[u"parentDeviceId"])]
            if u"brightnessLevel" in dev.states:
                valuesDict[u"parentDeviceDimmer"] = True
            else:
                valuesDict[u"parentDeviceDimmer"] = False
        return valuesDict

    ########################################
    # Device Com
    ######################
    def deviceStartComm(self, dev):
        self.parentDevIdsWeUseDict.append(int(dev.ownerProps[u"parentDeviceId"]))
        self._refreshState(dev)

    def deviceStopComm(self, dev):
        self.parentDevIdsWeUseDict.remove(int(dev.ownerProps[u"parentDeviceId"]))
        self._refreshState(dev)

    ########################################
    # Validation
    ######################
    def validateDeviceConfigUi(self, valuesDict, typeId, devId):
        errorDict = indigo.Dict()
        if typeId == u"virtualDeviceEnergyMeter":
            for value in valuesDict:
                #TODO: update these
                if value in [u"maxCurPower", u"minCurPower"]:
                    try:
                        valuesDict[value] = float(valuesDict[value])
                    except ValueError:
                        errorDict[value] = "The value of this field must be a number"
                        #errorDict["showAlertText"] = ""
                        valuesDict[value] = 0
                elif value == u"parentDeviceId":
                        valuesDict[value] = int(valuesDict[value])

        if errorDict:
            return (False, valuesDict, errorDict)
        else:
            return (True, valuesDict)

    ########################################
    # Methods for changes in Device states
    ########################################
    def deviceUpdated(self, origDev, newDev):
        ts = time.time()
        if u"parentDeviceId" in newDev.ownerProps:

            if origDev.configured != newDev.configured:
                self.deviceStartComm(newDev)
            elif origDev.enabled != newDev.enabled:
                if newDev.enabled:
                    self.deviceStartComm(origDev)
                else:
                    self.deviceStopComm(origDev)
            elif origDev.ownerProps['parentDeviceId'] != newDev.ownerProps['parentDeviceId']:
                self.parentDevIdsWeUseDict.remove(int(origDev.ownerProps[u"parentDeviceId"]))
                self.parentDevIdsWeUseDict.append(int(newDev.ownerProps[u"parentDeviceId"]))
                parentDevice = indigo.devices[int(origDev.ownerProps[u"parentDeviceId"])]
                if parentDevice.states['onOffState']:
                    if u"brightnessLevel" in parentDevice.states:
                        watts = self.getCurPower(origDev, int(parentDevice.states.get("brightnessLevel")))
                    else:
                        watts = float(origDev.ownerProps[u"powerAtOn"])
                    accumEnergyTotalTS = origDev.states.get("accumEnergyTotalTS", ts)
                    energy = ((ts - accumEnergyTotalTS) / 3600 * watts) / 1000
                else:
                    energy = 0
                self._addAccumEnergy(newDev, energy, ts)
                self._refreshState(newDev)
        if newDev.id not in self.parentDevIdsWeUseDict:
            return
        if (u"onOffState" in origDev.states and origDev.states['onOffState'] != newDev.states['onOffState'])\
                or (u"brightnessLevel" in origDev.states
                    and origDev.states['brightnessLevel'] != newDev.states['brightnessLevel']):
            self.logger.debug("The parent device has changed onOff state or brightness level")
            #TODO: Fix error handling if dev don't exists
            dev = filter(lambda x: x.ownerProps[u"parentDeviceId"] == str(origDev.id), indigo.devices.iter("self"))[0]
            if origDev.states['onOffState']:
                if u"brightnessLevel" in origDev.states:
                    watts = self.getCurPower(dev, int(origDev.states.get("brightnessLevel")))
                else:
                    watts = float(dev.ownerProps[u"powerAtOn"])
                accumEnergyTotalTS = dev.states.get("accumEnergyTotalTS", ts)
                energy = ((ts - accumEnergyTotalTS) / 3600 * watts) / 1000
            else:
                energy = 0
            self._addAccumEnergy(dev, energy, ts)
            self._refreshState(dev)

    def getCurPower(self, dev, dimLevel):
        xp = [1, 33, 66, 100]
        fp = [float(dev.ownerProps[u"powerAt1"]),
              float(dev.ownerProps[u"powerAt33"]),
              float(dev.ownerProps[u"powerAt66"]),
              float(dev.ownerProps[u"powerAt100"])]
        return np.interp(dimLevel, xp, fp)

    ########################################
    # General Action callback
    ######################
    def actionControlGeneral(self, action, dev):
        ###### BEEP ######
        if action.deviceAction == indigo.kDeviceGeneralAction.Beep:
            # Beep the hardware module (dev) here:
            # ** IMPLEMENT ME **
            indigo.server.log(u"sent \"%s\" %s" % (dev.name, "beep request"))

        ###### ENERGY UPDATE ######
        elif action.deviceAction == indigo.kDeviceGeneralAction.EnergyUpdate:
            # Request hardware module (dev) for its most recent meter data here:
            # ** IMPLEMENT ME **
            self._refreshState(dev, True)

        ###### ENERGY RESET ######
        elif action.deviceAction == indigo.kDeviceGeneralAction.EnergyReset:
            # Request that the hardware module (dev) reset its accumulative energy usage data here:
            # ** IMPLEMENT ME **
            indigo.server.log(u"sent \"%s\" %s" % (dev.name, "energy usage reset"))
            # And then tell Indigo to reset it by just setting the value to 0.
            # This will automatically reset Indigo's time stamp for the accumulation.
            dev.updateStateOnServer("accumEnergyTotal", 0.0)

        ###### STATUS REQUEST ######
        elif action.deviceAction == indigo.kDeviceGeneralAction.RequestStatus:
            # Query hardware module (dev) for its current status here:
            # ** IMPLEMENT ME **
            self._refreshState(dev, True)

    ########################################
    # Custom Plugin Action callbacks (defined in Actions.xml)
    ######################
    def setBacklightBrightness(self, pluginAction, dev):
        try:
            newBrightness = int(pluginAction.props.get(u"brightness", 100))
        except ValueError:
            # The int() cast above might fail if the user didn't enter a number:
            indigo.server.log(
                u"set backlight brightness action to device \"%s\" -- invalid brightness value" % (dev.name,),
                isError=True)
            return

        # Command hardware module (dev) to set backlight brightness here:
        # ** IMPLEMENT ME **
        sendSuccess = True  # Set to False if it failed.

        if sendSuccess:
            # If success then log that the command was successfully sent.
            indigo.server.log(u"sent \"%s\" %s to %d" % (dev.name, "set backlight brightness", newBrightness))

            # And then tell the Indigo Server to update the state:
            dev.updateStateOnServer("backlightBrightness", newBrightness)
        else:
            # Else log failure but do NOT update state on Indigo Server.
            indigo.server.log(u"send \"%s\" %s to %d failed" % (dev.name, "set backlight brightness", newBrightness),
                              isError=True)

    ########################################
    # Sensor Action callback
    ######################
    def actionControlSensor(self, action, dev):
        ###### TURN ON ######
        # Ignore turn on/off/toggle requests from clients since this is a read-only sensor.
        if action.sensorAction == indigo.kSensorAction.TurnOn:
            indigo.server.log(u"ignored \"%s\" %s request (sensor is read-only)" % (dev.name, "on"))
        # But we could request a sensor state update if we wanted like this:
        # dev.updateStateOnServer("onOffState", True)

        ###### TURN OFF ######
        # Ignore turn on/off/toggle requests from clients since this is a read-only sensor.
        elif action.sensorAction == indigo.kSensorAction.TurnOff:
            indigo.server.log(u"ignored \"%s\" %s request (sensor is read-only)" % (dev.name, "off"))
        # But we could request a sensor state update if we wanted like this:
        # dev.updateStateOnServer("onOffState", False)

        ###### TOGGLE ######
        # Ignore turn on/off/toggle requests from clients since this is a read-only sensor.
        elif action.sensorAction == indigo.kSensorAction.Toggle:
            indigo.server.log(u"ignored \"%s\" %s request (sensor is read-only)" % (dev.name, "toggle"))
            # But we could request a sensor state update if we wanted like this:
            # dev.updateStateOnServer("onOffState", not dev.onState)

    ########################################
    # Relay / Dimmer Action callback
    ######################
    def actionControlDimmerRelay(self, action, dev):
        ###### TURN ON ######
        if action.deviceAction == indigo.kDimmerRelayAction.TurnOn:
            # Command hardware module (dev) to turn ON here:
            # ** IMPLEMENT ME **
            sendSuccess = True  # Set to False if it failed.

            if sendSuccess:
                # If success then log that the command was successfully sent.
                indigo.server.log(u"sent \"%s\" %s" % (dev.name, "on"))

                # And then tell the Indigo Server to update the state.
                dev.updateStateOnServer("onOffState", True)
            else:
                # Else log failure but do NOT update state on Indigo Server.
                indigo.server.log(u"send \"%s\" %s failed" % (dev.name, "on"), isError=True)

        ###### TURN OFF ######
        elif action.deviceAction == indigo.kDimmerRelayAction.TurnOff:
            # Command hardware module (dev) to turn OFF here:
            # ** IMPLEMENT ME **
            sendSuccess = True  # Set to False if it failed.

            if sendSuccess:
                # If success then log that the command was successfully sent.
                indigo.server.log(u"sent \"%s\" %s" % (dev.name, "off"))

                # And then tell the Indigo Server to update the state:
                dev.updateStateOnServer("onOffState", False)
            else:
                # Else log failure but do NOT update state on Indigo Server.
                indigo.server.log(u"send \"%s\" %s failed" % (dev.name, "off"), isError=True)

        ###### TOGGLE ######
        elif action.deviceAction == indigo.kDimmerRelayAction.Toggle:
            # Command hardware module (dev) to toggle here:
            # ** IMPLEMENT ME **
            newOnState = not dev.onState
            sendSuccess = True  # Set to False if it failed.

            if sendSuccess:
                # If success then log that the command was successfully sent.
                indigo.server.log(u"sent \"%s\" %s" % (dev.name, "toggle"))

                # And then tell the Indigo Server to update the state:
                dev.updateStateOnServer("onOffState", newOnState)
            else:
                # Else log failure but do NOT update state on Indigo Server.
                indigo.server.log(u"send \"%s\" %s failed" % (dev.name, "toggle"), isError=True)

        ###### SET BRIGHTNESS ######
        elif action.deviceAction == indigo.kDimmerRelayAction.SetBrightness:
            # Command hardware module (dev) to set brightness here:
            # ** IMPLEMENT ME **
            newBrightness = action.actionValue
            sendSuccess = True  # Set to False if it failed.

            if sendSuccess:
                # If success then log that the command was successfully sent.
                indigo.server.log(u"sent \"%s\" %s to %d" % (dev.name, "set brightness", newBrightness))

                # And then tell the Indigo Server to update the state:
                dev.updateStateOnServer("brightnessLevel", newBrightness)
            else:
                # Else log failure but do NOT update state on Indigo Server.
                indigo.server.log(u"send \"%s\" %s to %d failed" % (dev.name, "set brightness", newBrightness),
                                  isError=True)

        ###### BRIGHTEN BY ######
        elif action.deviceAction == indigo.kDimmerRelayAction.BrightenBy:
            # Command hardware module (dev) to do a relative brighten here:
            # ** IMPLEMENT ME **
            newBrightness = dev.brightness + action.actionValue
            if newBrightness > 100:
                newBrightness = 100
            sendSuccess = True  # Set to False if it failed.

            if sendSuccess:
                # If success then log that the command was successfully sent.
                indigo.server.log(u"sent \"%s\" %s to %d" % (dev.name, "brighten", newBrightness))

                # And then tell the Indigo Server to update the state:
                dev.updateStateOnServer("brightnessLevel", newBrightness)
            else:
                # Else log failure but do NOT update state on Indigo Server.
                indigo.server.log(u"send \"%s\" %s to %d failed" % (dev.name, "brighten", newBrightness), isError=True)

        ###### DIM BY ######
        elif action.deviceAction == indigo.kDimmerRelayAction.DimBy:
            # Command hardware module (dev) to do a relative dim here:
            # ** IMPLEMENT ME **
            newBrightness = dev.brightness - action.actionValue
            if newBrightness < 0:
                newBrightness = 0
            sendSuccess = True  # Set to False if it failed.

            if sendSuccess:
                # If success then log that the command was successfully sent.
                indigo.server.log(u"sent \"%s\" %s to %d" % (dev.name, "dim", newBrightness))

                # And then tell the Indigo Server to update the state:
                dev.updateStateOnServer("brightnessLevel", newBrightness)
            else:
                # Else log failure but do NOT update state on Indigo Server.
                indigo.server.log(u"send \"%s\" %s to %d failed" % (dev.name, "dim", newBrightness), isError=True)

        ###### SET COLOR LEVELS ######
        elif action.deviceAction == indigo.kDimmerRelayAction.SetColorLevels:
            # action.actionValue is a dict containing the color channel key/value
            # pairs. All color channel keys (redLevel, greenLevel, etc.) are optional
            # so plugin should handle cases where some color values are not specified
            # in the action.
            actionColorVals = action.actionValue

            # Construct a list of channel keys that are possible for what this device
            # supports. It may not support RGB or may not support white levels, for
            # example, depending on how the device's properties (SupportsColor, SupportsRGB,
            # SupportsWhite, SupportsTwoWhiteLevels, SupportsWhiteTemperature) have
            # been specified.
            channelKeys = []
            usingWhiteChannels = False
            if dev.supportsRGB:
                channelKeys.extend(['redLevel', 'greenLevel', 'blueLevel'])
            if dev.supportsWhite:
                channelKeys.extend(['whiteLevel'])
                usingWhiteChannels = True
            if dev.supportsTwoWhiteLevels:
                channelKeys.extend(['whiteLevel2'])
            elif dev.supportsWhiteTemperature:
                channelKeys.extend(['whiteTemperature'])
            # Note having 2 white levels (cold and warm) takes precedence over
            # the user of a white temperature value. You cannot have both although
            # you can have a single white level and a white temperature value.

            # Next enumerate through the possible color channels and extract that
            # value from the actionValue (actionColorVals).
            keyValueList = []
            resultVals = []
            for channel in channelKeys:
                if channel in actionColorVals:
                    brightness = float(actionColorVals[channel])
                    brightnessByte = int(round(255.0 * (brightness / 100.0)))

                    # Command hardware module (dev) to change its color level here:
                    # ** IMPLEMENT ME **

                    if channel in dev.states:
                        keyValueList.append({'key': channel, 'value': brightness})
                    result = str(int(round(brightness)))
                elif channel in dev.states:
                    # If the action doesn't specify a level that is needed (say the
                    # hardware API requires a full RGB triplet to be specified, but
                    # the action only contains green level), then the plugin could
                    # extract the currently cached red and blue values from the
                    # dev.states[] dictionary:
                    cachedBrightness = float(dev.states[channel])
                    cachedBrightnessByte = int(round(255.0 * (cachedBrightness / 100.0)))
                    # Could show in the Event Log either '--' to indicate this level wasn't
                    # passed in by the action:
                    result = '--'
                # Or could show the current device state's cached level:
                #	result = str(int(round(cachedBrightness)))

                # Add a comma to separate the RGB values from the white values for logging.
                if channel == 'blueLevel' and usingWhiteChannels:
                    result += ","
                elif channel == 'whiteTemperature' and result != '--':
                    result += " K"
                resultVals.append(result)
            # Set to False if it failed.
            sendSuccess = True

            resultValsStr = ' '.join(resultVals)
            if sendSuccess:
                # If success then log that the command was successfully sent.
                indigo.server.log(u"sent \"%s\" %s to %s" % (dev.name, "set color", resultValsStr))

                # And then tell the Indigo Server to update the color level states:
                if len(keyValueList) > 0:
                    dev.updateStatesOnServer(keyValueList)
            else:
                # Else log failure but do NOT update state on Indigo Server.
                indigo.server.log(u"send \"%s\" %s to %s failed" % (dev.name, "set color", resultValsStr), isError=True)

    ########################################
    # Plugin Config callback
    ######################
    def closedPrefsConfigUi(self, valuesDict, userCancelled):
        if (not userCancelled):
            self.setLogLevel()

    def loggingLevelList(self, filter="", valuesDict=None, typeId="", targetId=0):
        logLevels = [
            [logging.DEBUG, "Debug"],
            (logging.INFO, "Normal"),
            (logging.WARN, "Warning"),
            (logging.ERROR, "Error"),
            (logging.CRITICAL, "Critical")
        ]
        return logLevels

    def setLogLevel(self):
        indigo.server.log(
            u"Setting logging level to %s" % (self.loggingLevelList()[self.pluginPrefs["loggingLevel"] / 10 - 1][1]))
        self.logger.setLevel(self.pluginPrefs.get("loggingLevel", logging.DEBUG))
        self.debug = (self.logger.level <= logging.DEBUG)