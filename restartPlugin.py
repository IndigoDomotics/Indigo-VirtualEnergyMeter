import sys, subprocess

print "sys.argv: %s " % str(sys.argv)
if len(sys.argv) != 2:
    print "Usage: restart_plugin.py /path/to/plugin/plugin.indigoPlugin\n"
else:
    plugin_id = sys.argv[1]
    print "calling restart_plugin with '%s'" % plugin_id
    plugin_script = '''plugin = indigo.server.getPlugin("%s")
if plugin.isEnabled():
   plugin.restart()
   return "Plugin %s restarted"
else:
   return "Plugin %s isn't enabled"
''' % (plugin_id, plugin_id, plugin_id)

    plugin_host_path = "/Library/Application Support/Perceptive Automation/Indigo 7/IndigoPluginHost.app/Contents/MacOS/IndigoPluginHost"
    subprocess.call([plugin_host_path, "-e", plugin_script])