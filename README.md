# Albula

A minimalist self-hosted music server.

## Current status

The library build is still wonky, I need to untangle scanning, metadata extraction etc and clean up. For now, complete rebuild is often the better option.

## Why not Plex / Subsonic / Airsonic / ...?

I just made Albula for myself because I disliked several things about the other options. Most likely, it will not be better than them for you. Some features to note though:

* Support for multiple artists per track / album artists per album / albums per track
* Less crowded interface
* Direct server-side scrobbling to Maloja, removing the need for individual solutions for each client
* No Javascript-bloated web interface
* No central authentication / phone-home

## Requirements

* Python 3
* Pip packages specified in `requirements.txt`
