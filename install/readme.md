Install of jumpscale 
=====================

use these install scripts to make your life easy

```
#if ubuntu is in recent state & apt get update was done recently
cd /tmp; rm -f install.sh; curl -k https://raw.githubusercontent.com/Jumpscale/jumpscale_core8/js8-with-js7/install/install.sh > install8.sh;bash install8.sh

```

to use in sandbox
-----------------
allways make sure you have set your env variables by
```
source /opt/jumpscale8/env.sh
```

to get shell
```
source /opt/jumpscale8/env.sh;python -c "from IPython import embed;embed()"
```

example through ipython
```
source /opt/jumpscale8/env.sh
ipython
from JumpScale import j
```

