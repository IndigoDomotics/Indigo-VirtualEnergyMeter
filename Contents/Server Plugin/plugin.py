#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################

import indigo
import random
import logging


class Plugin(indigo.PluginBase):
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        super(Plugin, self).__init__(pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
        self.logger.setLevel(logging.INFO)

    def startup(self):
        self.setLogLevel()
        self.logger.debug(u"startup called")

    def shutdown(self):
        self.logger.debug(u"shutdown called")

    def _refreshState(self, dev, logRefresh):
        # As an example here we update the current power (Watts) to a random
        # value, and we increase the kWh by a smidge.
        keyValueList = []
        if "curEnergyLevel" in dev.states:
            simulateWatts = random.randint(0, 500)
            simulateWattsStr = "%d W" % (simulateWatts)
            if logRefresh:
                indigo.server.log(u"received \"%s\" %s to %s" % (dev.name, "power load", simulateWattsStr))
            keyValueList.append({'key': 'curEnergyLevel', 'value': simulateWatts, 'uiValue': simulateWattsStr})

        if "accumEnergyTotal" in dev.states:
            simulateKwh = dev.states.get("accumEnergyTotal", 0) + 0.001
            simulateKwhStr = "%.3f kWh" % (simulateKwh)
            if logRefresh:
                indigo.server.log(u"received \"%s\" %s to %s" % (dev.name, "energy total", simulateKwhStr))
            keyValueList.append({'key': 'accumEnergyTotal', 'value': simulateKwh, 'uiValue': simulateKwhStr})

        dev.updateStatesOnServer(keyValueList)

    def runConcurrentThread(self):
        try:
            while True:
                for dev in indigo.devices.iter("self"):
                    if not dev.enabled or not dev.configured:
                        continue
                    # Plugins that need to poll out the status from the meter
                    # could do so here, then broadcast back the new values to the
                    # Indigo Server.
                self.sleep(5)
        except self.StopThread:
            pass  # Optionally catch the StopThread exception and do any needed cleanup.

    ########################################
    # Validation
    ######################
    def validateDeviceConfigUi(self, valuesDict, typeId, devId):
        return (True, valuesDict)

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