# Changelog

All notable changes to this project will be documented in this file.

## [2025-03-15]

### Fixed

- HTTP 405 Method Not Allowed errors by adding support for multiple HTTP methods on both `/webhook` and root `/` paths:
  - The webhook endpoint now accepts POST, GET, and HEAD requests
  - The root path now properly handles POST requests by forwarding them to the webhook handler
  - Added a `/favicon.ico` endpoint to properly handle favicon requests

- Fixed "channelId not found" errors:
  - Added support for responding directly to users via userId when channelId is not available
  - This enables better support for 1:1 chats and certain postback interactions

- Enhanced callback handling for template interactions:
  - Added a new handler specifically for template message button interactions
  - Improved detection of postback data in text messages
  - Added support for "ListTemplate_More" postback handling