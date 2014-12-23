#!/bin/sh

if [ -z "`ps axuw | grep [x]mms2d`" ]; then
	xmms2d -q &
	sleep 1
fi

psfm.py
