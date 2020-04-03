# Plan for autocrop API test
For this test, the plan is to wire the autocrop OpenCV model to a simple API. We'll make it so it can read in image URLs or has image data as part of the header.

# Requirements & Features

## Requirements
### Refactoring
* crop and crop_uri DRY internals
* Enforce size limit

### Logging
* Get file details
### Demo tier
* Size limit at 20 MB
    - Error "This demo app has a size limit of 1MB per upload. Please see {{ LANDING_PAGE }} to purchase a subscription."
* No JWT
* Logging model internals (e.g. audit)
    - Logging when scaling is used would be a good test

### Paid tier
* Size limit at 20 MB
    - Error "This size limit has been set in settings. To bypass, go to settings {{ ADMIN_PAGE_URL }}#size_limit or contact this API's administrator {{ CONTACT_PAGE__URL }}."
* Uses JWT
* User creation
    - Module in the admin panel, located at {{ URL }}/admin#users
    - Not on by default
    - This API needs to connect to database
    - Needs auth connectors
* Logging model internals (e.g. audit)
    - Logging when scaling is used would be a good test
## Features
* Read from URL
* Read from header

## Other
R-spec for Python?
