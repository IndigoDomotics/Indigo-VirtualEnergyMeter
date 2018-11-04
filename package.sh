#!/usr/bin/env bash
PLUGIN_NAME=${PWD##*/}
mkdir "$PLUGIN_NAME.indigoplugin"
cp -r Contents/ "$PLUGIN_NAME.indigoplugin/Contents"
zip -r "$PLUGIN_NAME.indigoplugin.zip" "$PLUGIN_NAME.indigoplugin/"
rm -rf "$PLUGIN_NAME.indigoplugin"