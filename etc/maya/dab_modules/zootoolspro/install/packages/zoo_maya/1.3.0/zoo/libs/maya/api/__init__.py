"""Maya api Package revolving around general operations for api queries and state changes. Most functions do not do any
 safety checks (try/except) they do expect you to know what you're doing. Any safety checks should be done by the client
 of the function. This is by design, the only exception is when certain operations have a high chance of a crash.

"""