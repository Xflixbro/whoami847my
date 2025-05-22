#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#

import os
from os import environ, getenv
import logging
from logging.handlers import RotatingFileHandler
from pyrogram import filters
from database.database import db  # Updated import

# MehediYT69
# --------------------------------------------
# Bot token @Botfather
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
APP_ID = int(os.environ.get("APP_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
#--------------------------------------------

CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1002170811388"))  # Your db channel Id
OWNER = os.environ.get("OWNER", "MehediYT69")  # Owner username without @
OWNER_ID = int(os.environ.get("OWNER_ID", "7328629001"))  # Owner id
#--------------------------------------------
PORT = os.environ.get("PORT", "8080")
#--------------------------------------------
DB_URI = os.environ.get("DATABASE_URL", "")
DB_NAME = os.environ.get("DATABASE_NAME", "animelord")
# --------------------------------------------
FSUB_LINK_EXPIRY = int(getenv("FSUB_LINK_EXPIRY", "10"))  # 0 means no expiry
BAN_SUPPORT = os.environ.get("BAN_SUPPORT", "https://t.me/CodeflixSupport")
TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "200"))
# --------------------------------------------
START_PIC = os.environ.get("START_PIC", "https://telegra.ph/file/ec17880d61180d3312d6a.jpg")
FORCE_PIC = os.environ.get("FORCE_PIC", "https://telegra.ph/file/e292b12890b8b4b9dcbd1.jpg")

# --------------------------------------------
# List of images for random selection in /start, /help, /about
RANDOM_IMAGES = [
    "https://i.postimg.cc/4xHskCC4/46c05f19.jpg",
    "https://i.postimg.cc/Tw0Xqfb0/0cf8d2b4.jpg",
    "https://i.postimg.cc/FsBNBrBn/c1462d7c.jpg",
    "https://i.postimg.cc/43CZX8Z6/5d504620.jpg",
    "https://i.postimg.cc/vZnF2W9c/14f628c9.jpg",
    "https://i.postimg.cc/fb0LKtWK/10a9048d.jpg",
    "https://i.postimg.cc/qMjzMHZ8/575cb6f0.jpg",
    "https://i.postimg.cc/dVgQLsRT/db05f565.jpg",
    "https://i.postimg.cc/rmNqn5BS/102cf50e.jpg",
    "https://i.postimg.cc/zGyXzbhr/0a766a2f.jpg",
    "https://i.postimg.cc/FFG90ggv/e1d2e1f2.jpg",
    "https://i.postimg.cc/zfWzhsp2/66d97798.jpg",
    "https://i.postimg.cc/brYpKsP4/d4f98d5a.jpg",
    "https://i.postimg.cc/MKTz5MdQ/81d869a5.jpg",
    "https://i.postimg.cc/3NwQtVCT/9fdeb5c9.jpg",
    "https://i.postimg.cc/SxPRC74R/99e8163f.jpg",
    "https://i.postimg.cc/qBmTNB4M/aa7dd766.jpg",
    "https://i.postimg.cc/65jpxLyc/94c57311.jpg",
    "https://i.postimg.cc/Wbb1yfbt/0f0deb92.jpg",
    "https://i.postimg.cc/Hsprgk3Y/212a6a5b.jpg",
    "https://i.postimg.cc/Dw0mSptR/31b251b9.jpg",
    "https://i.postimg.cc/jqhjZrTG/48030f75.jpg",
    "https://i.postimg.cc/50VxSsR4/76ed71fa.jpg",
    "https://i.postimg.cc/V6qkxxC0/25e719d1.jpg",
    "https://i.postimg.cc/FzGsR0G9/9c0a1ea8.jpg",
    "https://i.postimg.cc/j5PDsWG5/83432626.jpg",
    "https://i.postimg.cc/vmdRJcLX/2dfda6e8.jpg",
    "https://i.postimg.cc/PqzGTTSH/498fcce7.jpg",
    "https://i.postimg.cc/Fzn58pDJ/9d0a4fc7.jpg",
    "https://i.postimg.cc/PxTjwPCN/bdd62783.jpg",
    "https://i.postimg.cc/7hBwDwYh/58fa4cc6.jpg",
    "https://i.postimg.cc/RhvZ4g7s/cc69117b.jpg",
    "https://i.postimg.cc/1thzYmfZ/bbbe6603.jpg",
    "https://i.postimg.cc/J4vCQTsf/1257f018.jpg",
    "https://i.postimg.cc/VNjwvjL3/48bf3e8d.jpg",
    "https://i.postimg.cc/mDbvrJnH/eeed170c.jpg",
    "https://i.postimg.cc/MTdhftkr/e029ee80.jpg",
    "https://i.postimg.cc/vZfktGFn/3f869668.jpg",
    "https://i.postimg.cc/fWqGwHfV/516a74c9.jpg",
    "https://i.postimg.cc/qqqWsn4B/1395ce7b.jpg",
    "https://i.postimg.cc/Yq4Jj1db/b613ac63.jpg",
    "https://i.postimg.cc/nL1WNTLc/73e88967.jpg",
    "https://i.postimg.cc/4NmTVCxv/1fcbe8f6.jpg",
    "https://i.postimg.cc/pLL5DLnG/3e993824.jpg",
    "https://i.postimg.cc/DytRG8DF/e1cec8b1.jpg",
    "https://i.postimg.cc/XqBQNgn5/2696d39a.jpg",
    "https://i.postimg.cc/qMLCh3g6/3465e06d.jpg",
    "https://i.postimg.cc/43rKkv2q/74240ce0.jpg",
    "https://i.postimg.cc/XYf1yxdc/b98c439c.jpg",
    "https://i.postimg.cc/T1KHL6Jp/a5c9557b.jpg",
    "https://i.postimg.cc/137nM1G9/ee417b3f.jpg",
    "https://i.postimg.cc/NMfntTy8/659f4d33.jpg",
    "https://i.postimg.cc/3NhdW8TZ/9c0aa53b.jpg",
    "https://i.postimg.cc/d3fp41V2/e3bfac99.jpg",
    "https://i.postimg.cc/VNwT72mV/779757b6.jpg",
    "https://i.postimg.cc/FR8wxzRj/952d606c.jpg",
    "https://i.postimg.cc/vmXP0BP4/2aad0a31.jpg",
    "https://i.postimg.cc/wB9f5JkK/e4240ea9.jpg",
    "https://i.postimg.cc/qMXZNj8c/2a51715f.jpg",
    "https://i.postimg.cc/zGZPB4bG/9c82f40e.jpg",
    "https://i.postimg.cc/J0SYj2pK/a9ead2c6.jpg",
    "https://i.postimg.cc/RqrGWn0D/e5b56802.jpg",
    "https://i.postimg.cc/T2ss8KTm/51097ed2.jpg",
    "https://i.postimg.cc/9M8nQMT6/8905fb2f.jpg",
    "https://i.postimg.cc/59HVFd0B/04db1eda.jpg",
    "https://i.postimg.cc/qB9dsbh9/89ce6a9b.jpg",
    "https://i.postimg.cc/ncBf04qM/7a4e7d7a.jpg",
    "https://i.postimg.cc/RZm58WTd/64b805c0.jpg",
    "https://i.postimg.cc/Rhtypm62/67a76361.jpg",
    "https://i.postimg.cc/jq6Dm7H3/fe092523.jpg",
    "https://i.postimg.cc/ZKk1BWXm/2b83b007.jpg",
    "https://i.postimg.cc/MKjFzzGL/3d8fb53d.jpg",
    "https://i.postimg.cc/cHHF2SjX/1e4ae3e1.jpg",
    "https://i.postimg.cc/LXbxMWFR/279c487a.jpg",
    "https://i.postimg.cc/Vkmpg3YH/0bc38a2c.jpg",
    "https://i.postimg.cc/NjxqwQJc/88cdd94d.jpg",
    "https://i.postimg.cc/26sXZtcG/f546cc19.jpg",
    "https://i.postimg.cc/h4mYBSv5/2e7b01b7.jpg",
    "https://i.postimg.cc/CMn3xGPJ/a0cdf270.jpg",
    "https://i.postimg.cc/R0VrS2yn/650aa8db.jpg",
    "https://i.postimg.cc/DyqRq2KX/5db403d1.jpg",
    "https://i.postimg.cc/255JRhLQ/21599625.jpg",
    "https://i.postimg.cc/SKtPyRcw/ad3d1061.jpg",
    "https://i.postimg.cc/CLNmhdgm/32c69053.jpg",
    "https://i.postimg.cc/g0MCnNbt/ed51007f.jpg",
    "https://i.postimg.cc/zfMhDYvd/a850eef8.jpg",
    "https://i.postimg.cc/8z430tck/dee1b267.jpg",
    "https://i.postimg.cc/QtHR51X8/edca889e.jpg",
    "https://i.postimg.cc/gkdZ2DcP/06d717fc.jpg",
    "https://i.postimg.cc/XJGzXW8X/cb38bc63.jpg",
    "https://i.postimg.cc/cCc6np1G/6f84e601.jpg",
    "https://i.postimg.cc/NfwzGWrf/dbd33d8c.jpg",
    "https://i.postimg.cc/wMD4cknp/0795c569.jpg",
    "https://i.postimg.cc/Zq99MsH6/7267fabd.jpg",
    "https://i.postimg.cc/cC7tcKmj/471efead.jpg",
    "https://i.postimg.cc/4xfVB1j1/6e9c1ae9.jpg",
    "https://i.postimg.cc/zBggV2Rq/7dab5c7e.jpg",
    "https://i.postimg.cc/dQGCFXYB/0f8cc5bb.jpg",
    "https://i.postimg.cc/GmXYNyCn/74195d8b.jpg",
    "https://i.postimg.cc/8CsWVzpJ/c9e6433f.jpg",
    "https://i.postimg.cc/KjhgL7nB/c6f8d075.jpg",
    "https://i.postimg.cc/SxxVJqQq/e250cc30.jpg",
    "https://i.postimg.cc/2S9GWJ3W/86c12c22.jpg",
    "https://i.postimg.cc/GpBQxQs5/4347d44d.jpg",
    "https://i.postimg.cc/CKW4PqGL/a1d81652.jpg",
    "https://i.postimg.cc/mZ3SjhtB/f159f803.jpg",
    "https://i.postimg.cc/5NxSR1Cv/2ade38d8.jpg",
    "https://i.postimg.cc/qqrx0HDP/c87e004b.jpg",
    "https://i.postimg.cc/xCvL6Fjt/ff1bd9d8.jpg",
    "https://i.postimg.cc/MpHbzDtp/a822def4.jpg",
    "https://i.postimg.cc/hG7LdtkF/bebd4829.jpg",
    "https://i.postimg.cc/bJcQHjPZ/f6e10807.jpg",
    "https://i.postimg.cc/brRHwVKs/c025704e.jpg",
    "https://i.postimg.cc/cLz7Cn5M/3f8fb144.jpg",
    "https://i.postimg.cc/jdZ4V9H1/0227c398.jpg",
    "https://i.postimg.cc/vTXfsgVn/f1c9f8c4.jpg",
    "https://i.postimg.cc/2jx4vJK5/e2d47193.jpg",
    "https://i.postimg.cc/MKK1YDCm/095ef58c.jpg",
    "https://i.postimg.cc/65jnbZwJ/61a3313b.jpg",
    "https://i.postimg.cc/nrV90FPh/ef02c732.jpg",
    "https://i.postimg.cc/L8Gf2Mnx/8bf97b85.jpg",
    "https://i.postimg.cc/8CWvCnvN/11b3f90d.jpg",
    "https://i.postimg.cc/DwSs9zyW/59de3be9.jpg",
    "https://i.postimg.cc/85mrRJwY/d8051d86.jpg",
    "https://i.postimg.cc/gJWZLqyR/5e3bd993.jpg",
    "https://i.postimg.cc/X7Jy5v52/d7f30018.jpg",
    "https://i.postimg.cc/V6gdrykQ/24f1cf81.jpg",
    "https://i.postimg.cc/hvGhVCXJ/a0138e8e.jpg",
    "https://i.postimg.cc/xT4N3Sy9/5dbae481.jpg",
    "https://i.postimg.cc/d1whVQvj/cf5e3dd2.jpg",
    "https://i.postimg.cc/qBQ3gKNh/442031a3.jpg",
    "https://i.postimg.cc/g2LXMBN8/1af6e5d7.jpg",
    "https://i.postimg.cc/vmR1CLNj/88550455.jpg",
    "https://i.postimg.cc/HnScNqq4/74d32c85.jpg",
    "https://i.postimg.cc/q78tr6f7/d9486247.jpg",
    "https://i.postimg.cc/D0Y06qGx/ad778d88.jpg",
    "https://i.postimg.cc/tCYYTM0w/6bb4bfea.jpg",
    "https://i.postimg.cc/7YdbTnw6/aa76decb.jpg",
    "https://i.postimg.cc/mg9k31gS/5d97c319.jpg",
    "https://i.postimg.cc/W464CRrF/49dda337.jpg",
    "https://i.postimg.cc/vB0Z8W0G/fc387791.jpg",
    "https://i.postimg.cc/tgHTBR1G/e41aced2.jpg",
    "https://i.postimg.cc/RFS0zPQP/d62a0e07.jpg",
    "https://i.postimg.cc/HWSrTCNb/d7c0c7cd.jpg",
    "https://i.postimg.cc/qqgMNzFy/85a6c488.jpg",
    "https://i.postimg.cc/2jXSP7qw/1343c5a2.jpg",
    "https://i.postimg.cc/5NhNt9SQ/6c439193.jpg",
    "https://i.postimg.cc/vZ58xR0q/c0349d60.jpg",
    "https://i.postimg.cc/0Nxkpt38/7b101e3e.jpg",
    "https://i.postimg.cc/SKryV6Fc/38deb63e.jpg",
    "https://i.postimg.cc/yxJsV2JT/c0ad3b61.jpg",
    "https://i.postimg.cc/qMhv06yd/5a3edfac.jpg",
    "https://i.postimg.cc/yd87GDst/bebb772e.jpg",
    "https://i.postimg.cc/Y0Jkj8YB/22c2aa2d.jpg",
    "https://i.postimg.cc/k4Y7P754/100405d7.jpg",
    "https://i.postimg.cc/9QHCh8cG/cc9e62d2.jpg",
    "https://i.postimg.cc/HWKTSWKv/79b84a29.jpg",
    "https://i.postimg.cc/Mp0xK7Gg/77e74502.jpg",
    "https://i.postimg.cc/YqWMTKBr/96697aed.jpg",
    "https://i.postimg.cc/mrb4cPzk/2d4d0034.jpg",
    "https://i.postimg.cc/6QYXCBn0/5915e7be.jpg",
    "https://i.postimg.cc/k4GdcLyd/f21e60a1.jpg",
    "https://i.postimg.cc/26tNXTHL/dd853107.jpg",
    "https://i.postimg.cc/x8bVrH7x/3a6cfbba.jpg",
    "https://i.postimg.cc/8sQQTcg1/aeae86d3.jpg",
    "https://i.postimg.cc/tR1sRcGf/5e4e161f.jpg",
    "https://i.postimg.cc/tRLYszXg/bb0d0def.jpg",
    "https://i.postimg.cc/xTMqMbC3/13a0cb0e.jpg",
    "https://i.postimg.cc/x1PCFDLk/49c88b91.jpg",
    "https://i.postimg.cc/FKsKMWxT/1f6d106b.jpg",
    "https://i.postimg.cc/t4bJ5CnQ/6c6b9dc9.jpg",
    "https://i.postimg.cc/WzrpGQ21/876bc1a1.jpg",
    "https://i.postimg.cc/JnS4B1CF/d0c05301.jpg",
    "https://i.postimg.cc/638p38gR/a45cd523.jpg",
    "https://i.postimg.cc/bvCvpxCp/a9bf4256.jpg",
    "https://i.postimg.cc/tCQ4qC5Z/253a7d30.jpg",
    "https://i.postimg.cc/vHrHcFqP/6028a1cc.jpg",
    "https://i.postimg.cc/htMD18qT/63ccb8e4.jpg",
    "https://i.postimg.cc/DzM7t20z/5964770e.jpg",
    "https://i.postimg.cc/xCN9QWN3/0c1635b6.jpg",
    "https://i.postimg.cc/g0JYSwY5/a2f8bc5f.jpg",
    "https://i.postimg.cc/x19jmxB9/83c151ad.jpg",
    "https://i.postimg.cc/5ycb2nwd/d57d095f.jpg",
    "https://i.postimg.cc/6qdw2n07/e9c44c35.jpg",
    "https://i.postimg.cc/3rp3cQTK/86917702.jpg",
    "https://i.postimg.cc/7Ynwq1hd/2be5529b.jpg",
    "https://i.postimg.cc/65XBsbWC/c5067a0f.jpg",
    "https://i.postimg.cc/XYN3qZyJ/57b6e51c.jpg",
    "https://i.postimg.cc/t4rbxXhz/47140c62.jpg",
    "https://i.postimg.cc/C18pXk9v/0d30ad94.jpg",
    "https://i.postimg.cc/L4zMVkt5/22f79f8c.jpg",
    "https://i.postimg.cc/mrts30jW/581de5f9.jpg",
    "https://i.postimg.cc/sx9dDyj7/5930039c.jpg",
    "https://i.postimg.cc/6QgNMYb2/3295ec95.jpg",
    "https://i.postimg.cc/VvcP858z/1558ea6f.jpg",
    "https://i.postimg.cc/xTnVpk5R/c43ad9b1.jpg",
    "https://i.postimg.cc/9Fb56WNj/b1fa45c6.jpg",
    "https://i.postimg.cc/R0jj7qqw/1c735d43.jpg",
    "https://i.postimg.cc/7LCFJSPx/9078a851.jpg",
    "https://i.postimg.cc/fRbnZ66S/18337325.jpg",
    "https://i.postimg.cc/GmS0pXC7/bc0275fb.jpg",
    "https://i.postimg.cc/VvwphTq6/e7d25b3a.jpg",
    "https://i.postimg.cc/k4KLf9tz/7d5ff0fa.jpg",
    "https://i.postimg.cc/BbCkfgpC/2e3fe32f.jpg",
    "https://i.postimg.cc/tRdL6qbV/73b26a18.jpg",
    "https://i.postimg.cc/52yGD8Cw/52ef2a76.jpg",
    "https://i.postimg.cc/qvFYrgsW/4bf7f8ce.jpg",
    "https://i.postimg.cc/JnV2ygdq/94b95e19.jpg",
    "https://i.postimg.cc/5tFr21py/40c7e46b.jpg",
    "https://i.postimg.cc/QtQncb2r/1e1d7a15.jpg",
    "https://i.postimg.cc/vTXqNm8q/eb7f4e95.jpg",
    "https://i.postimg.cc/59mR0s5B/c1c1e2eb.jpg",
    "https://i.postimg.cc/2yC9GWYL/aabbbafb.jpg",
    "https://i.postimg.cc/dttSTGnz/968861c6.jpg",
    "https://i.postimg.cc/yYQphWbW/68712d5f.jpg",
    "https://i.postimg.cc/nhXR3Zy2/f0932cdc.jpg",
    "https://i.postimg.cc/13bWT2PQ/03d30eea.jpg",
    "https://i.postimg.cc/q7nmdwMC/53d2c481.jpg",
    "https://i.postimg.cc/XJbsN5p1/8d1cbe78.jpg",
    "https://i.postimg.cc/Jn5PshXr/6d7f494a.jpg",
    "https://i.postimg.cc/kGMwKdNx/64589744.jpg",
    "https://i.postimg.cc/kXpw6z2b/deccc26b.jpg",
    "https://i.postimg.cc/br6gRFL4/3c774f4c.jpg",
    "https://i.postimg.cc/qBQ10z0Q/da247890.jpg",
    "https://i.postimg.cc/kX4f5qgC/079f84fa.jpg",
    "https://i.postimg.cc/R0cTY0X7/c7f2088b.jpg",
    "https://i.postimg.cc/jSnczcfk/e3f8869d.jpg",
    "https://i.postimg.cc/QMLbS7kN/6a03d853.jpg",
    "https://i.postimg.cc/Wz46twj8/ffdf6615.jpg",
    "https://i.postimg.cc/1tBr9jx4/aa791aa1.jpg",
    "https://i.postimg.cc/V6mFPcV3/a94fae29.jpg",
    "https://i.postimg.cc/RCPLyyQD/ed11318a.jpg",
    "https://i.postimg.cc/T1Hjb536/cd8f313e.jpg",
    "https://i.postimg.cc/jdL4bcMd/515a81b6.jpg",
    "https://i.postimg.cc/ZK2FKNQP/a091e45a.jpg",
    "https://i.postimg.cc/nhmKsz8y/fff0b102.jpg",
    "https://i.postimg.cc/VNcqX8md/db5db895.jpg",
    "https://i.postimg.cc/tgth5M4D/b492e958.jpg",
    "https://i.postimg.cc/SsSctfX4/f0cdfef2.jpg",
    "https://i.postimg.cc/cHFfqtYn/0bfa4e6d.jpg",
    "https://i.postimg.cc/NFLmQG7P/d78276a2.jpg",
    "https://i.postimg.cc/KcstJLmX/8ffbf8a5.jpg",
    "https://i.postimg.cc/L57f5dx4/542fe3ef.jpg",
    "https://i.postimg.cc/wTyLPvB1/788a9551.jpg",
    "https://i.postimg.cc/65knNX7Y/2e5cb5ff.jpg",
    "https://i.postimg.cc/GmvYL5Gr/146ef4be.jpg",
    "https://i.postimg.cc/Y9DLDKKN/959489df.jpg",
    "https://i.postimg.cc/4dxh14MN/ff5e2d0c.jpg",
    "https://i.postimg.cc/x8kJWxnw/2a479e8b.jpg",
    "https://i.postimg.cc/vTpgMrmc/01e2ca16.jpg",
    "https://i.postimg.cc/DfDbqTcn/c756ad5a.jpg",
    "https://i.postimg.cc/kgP6pvZH/be8a5dbc.jpg",
    "https://i.postimg.cc/02wKnBtm/e1623921.jpg",
    "https://i.postimg.cc/9QPR5qHQ/d221f9cb.jpg",
    "https://i.postimg.cc/4359tHWS/b62003ce.jpg",
    "https://i.postimg.cc/bv3ZdcJX/4b616525.jpg",
    "https://i.postimg.cc/vT6TP4vM/2c258f54.jpg",
    "https://i.postimg.cc/MTHvQPMn/0905dfe3.jpg",
    "https://i.postimg.cc/grFJ1GMh/656439c4.jpg",
    "https://i.postimg.cc/zD9FqW6C/1ea203a3.jpg",
    "https://i.postimg.cc/SQXG0VTQ/d217a00d.jpg",
    "https://i.postimg.cc/qvrc3rkg/cc45deea.jpg",
    "https://i.postimg.cc/bNkHrrfK/3f8f8d03.jpg",
    "https://i.postimg.cc/vBKDLrf3/cc46e0c3.jpg",
    "https://i.postimg.cc/FHxyb6Rp/ce62c645.jpg",
    "https://i.postimg.cc/1zCD2NDN/bbd8af45.jpg",
    "https://i.postimg.cc/j5Dybdh3/d83084ea.jpg",
    "https://i.postimg.cc/JnSZ4V6r/1805ef1f.jpg",
    "https://i.postimg.cc/FFJ0Czz7/cf9a4b9a.jpg",
    "https://i.postimg.cc/tCQWKbnD/332483d2.jpg",
    "https://i.postimg.cc/WzrrdWCM/9e26ce03.jpg",
    "https://i.postimg.cc/KvPBFWnb/64c18e2a.jpg",
    "https://i.postimg.cc/4xXt3159/76ecf230.jpg",
    "https://i.postimg.cc/SxV9YzTt/dfcc479f.jpg",
    "https://i.postimg.cc/bvNQmRSh/a13568c8.jpg",
    "https://i.postimg.cc/bvJtxN4Y/30be186c.jpg",
    "https://i.postimg.cc/8C0rtgVR/933d6a7a.jpg",
    "https://i.postimg.cc/4dHH02Jr/21495dbd.jpg",
    "https://i.postimg.cc/Y0cLBN0j/8d27b401.jpg",
    "https://i.postimg.cc/qBnCXFDK/c7e95e67.jpg",
    "https://i.postimg.cc/HnQcYJ8z/be7958fb.jpg",
    "https://i.postimg.cc/RZP3Zxhk/1e53f5dd.jpg",
    "https://i.postimg.cc/zGDbNGzw/9a139ddb.jpg",
    "https://i.postimg.cc/yYyg2ZHY/8b65cf41.jpg",
    "https://i.postimg.cc/SNhYZGHv/998c0daf.jpg"
]

SHORTLINK_URL = os.environ.get("SHORTLINK_URL", "linkshortify.com")
SHORTLINK_API = os.environ.get("SHORTLINK_API", "")
TUT_VID = os.environ.get("TUT_VID", "https://t.me/hwdownload/3")
SHORT_MSG = "<b>⌯ Here is Your Download Link, Must Watch Tutorial Before Clicking On Download...</b>"

SHORTENER_PIC = os.environ.get("SHORTENER_PIC", "https://telegra.ph/file/ec17880d61180d3312d6a.jpg")
# --------------------------------------------

# --------------------------------------------
HELP_TXT = os.environ.get("HELP_TXT","<blockquote><b>ʜᴇʟʟᴏ {first}<b/></blockquote>\n\n<b><blockquote>◈ ᴛʜɪs ɪs ᴀɴ ғɪʟᴇ ᴛᴏ ʟɪɴᴋ ʙᴏᴛ ᴡᴏʀᴋ ғᴏʀ @MehediYT69\n\n❏ ʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅs\n├/start : sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ\n├/about : ᴏᴜʀ Iɴғᴏʀᴍᴀᴛɪᴏɴ\n├/commands : ꜰᴏʀ ɢᴇᴛ ᴀʟʟ ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅs ʟɪꜱᴛ\n└/help : ʜᴇʟᴘ ʀᴇʟᴀᴛᴇᴅ ʙᴏᴛ\n\n sɪᴍᴘʟʏ ᴄʟɪᴄᴋ ᴏɴ ʟɪɴᴋ ᴀɴᴅ sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ ᴊᴏɪɴ ʙᴏᴛʜ ᴄʜᴀɴɴᴇʟs ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ ᴛʜᴀᴛs ɪᴛ.....!\n\n ᴅᴇᴠᴇʟᴏᴘᴇᴅ ʙʏ <a href=https://t.me/Anime_Lord_Bots>Aɴɪᴍᴇ Lᴏʀᴅ</a></blockquote></b>")
ABOUT_TXT = os.environ.get("ABOUT_TXT","<blockquote><b>ʜᴇʟʟᴏ {first}<b/></blockquote>\n\n<b><blockquote>◈ ᴄʀᴇᴀᴛᴏʀ: <a href=https://t.me/Anime_Lord_Bots>MehediYT</a>\n◈ ꜰᴏᴜɴᴅᴇʀ ᴏꜰ : <a href=@who_am_i_69>WHO-AM-I</a>\n◈ ᴀɴɪᴍᴇ ᴄʜᴀɴɴᴇʟ : <a href=https://t.me/Anime_Lord_Official>Aɴɪᴍᴇ Lᴏʀᴅ</a>\n◈ sᴇʀɪᴇs ᴄʜᴀɴɴᴇʟ : <a href=https://t.me/Anime_Lord_Series>Aɴɪᴍᴇ Lᴏʀᴅ sᴇʀɪᴇs ғʟɪx</a>\n◈ ᴀᴅᴜʟᴛ ᴍᴀɴʜᴡᴀ : <a href=https://t.me/Anime_Lord_Hentai>Aɴɪᴍᴇ Lᴏʀᴅ Pᴏʀɴʜᴡᴀs</a>\n◈ ᴅᴇᴠᴇʟᴏᴘᴇʀ : <a href=https://t.me/Anime_Lord_Bots>Aɴɪᴍᴇ Lᴏʀᴅ</a></blockquote></b>")
# --------------------------------------------
START_MSG = os.environ.get("START_MESSAGE", "<blockquote><b>ʜᴇʟʟᴏ {first}</b></blockquote>\n\n<blockquote><b> ɪ ᴀᴍ ғɪʟᴇ sᴛᴏʀᴇ ʙᴏᴛ ᴄʀᴇᴀᴛᴇᴅ ʙʏ  <a href=https://t.me/Anime_Lord_Official>Aɴɪᴍᴇ Lᴏʀᴅ</a>, ɪ ᴄᴀɴ sᴛᴏʀᴇ ᴘʀɪᴠᴀᴛᴇ ғɪʟᴇs ɪɴ sᴘᴇᴄɪғɪᴇᴅ ᴄʜᴀɴɴᴇʟ ᴀɴᴅ ᴏᴛʜᴇʀ ᴜsᴇʀs ᴄᴀɴ ᴀᴄᴄᴇss ɪᴛ ғʀᴏᴍ sᴘᴇᴄɪᴀʟ ʟɪɴᴋ.</blockquote></b>")
FORCE_MSG = os.environ.get("FORCE_SUB_MESSAGE", "ʜᴇʟʟᴏ {first}\n\n<b>ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟs ᴀɴᴅ ᴛʜᴇɴ ᴄʟɪᴄᴋ ᴏɴ ʀᴇʟᴏᴀᴅ button ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛᴇᴅ ꜰɪʟᴇ.</b>")

CMD_TXT = """<blockquote><b>» ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅs:</b></blockquote>

<b>›› /auto_delete :</b> ᴍᴀɴᴀɢᴇ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ sᴇᴛᴛɪɴɢs
<b>›› /dbroadcast :</b> ʙʀᴏᴀᴅᴄᴀsᴛ ᴅᴏᴄᴜᴍᴇɴᴛ / ᴠɪᴅᴇᴏ
<b>›› /ban :</b> ʙᴀɴ ᴀ ᴜꜱᴇʀ
<b>›› /unban :</b> ᴜɴʙᴀɴ ᴀ ᴜꜱᴇʀ
<b>›› /banlist :</b> ɢᴇᴛ ʟɪsᴛ ᴏꜰ ʙᴀɴɴᴇᴅ ᴜꜱᴇʀs
<b>›› /addchnl :</b> ᴀᴅᴅ ꜰᴏʀᴄᴇ sᴜʙ ᴄʜᴀɴɴᴇʟ
<b>›› /delchnl :</b> ʀᴇᴍᴏᴠᴇ ꜰᴏʀᴄᴇ sᴜʙ ᴄʜᴀɴɴᴇʟ
<b>›› /listchnl :</b> ᴠɪᴇᴡ ᴀᴅᴅᴇᴅ ᴄʜᴀɴɴᴇʟs
<b>›› /fsub_mode :</b> ᴛᴏɢɢʟᴇ ꜰᴏʀᴄᴇ sᴜʙ ᴍᴏᴅᴇ
<b>›› /pbroadcast :</b> sᴇɴᴅ ᴘʜᴏᴛᴏ ᴛᴏ ᴀʟʟ ᴜsᴇʀs
<b>›› /add_admin :</b> ᴀᴅᴅ ᴀɴ ᴀᴅᴍɪɴ
<b>›› /deladmin :</b> ʀᴇᴍᴏᴠᴇ ᴀɴ ᴀᴅᴍɪɴ
<b>›› /admins :</b> ɢᴇᴛ ʟɪsᴛ ᴏꜴ ᴀᴅᴍɪɴs
<b>›› /addpremium :</b> ᴀᴅᴅ ᴀ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀ
<b>›› /delpremium :</b> ʀᴇᴍᴏᴠᴇ ᴀ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀ
<b>›› /premiumusers :</b> ɢᴇᴛ ʟɪsᴛ ᴏꜰ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀs
<b>›› /broadcast :</b> ʙʀᴏᴀᴅᴄᴀsᴛ ᴍᴇssᴀɢᴇ ᴛᴏ ᴀʟʟ ᴜsᴇʀs
<b>›› /stats :</b> ɢᴇᴛ ʙᴏᴛ sᴛᴀᴛs
<b>›› /logs :</b> ɢᴇᴛ ʟᴏɢs ᴏꜰ ʙᴏᴛ
<b>›› /setvar :</b> sᴇᴛ ᴇɴᴠɪʀᴏɴᴍᴇɴᴛ ᴠᴀʀɪᴀʙʟᴇ
<b>›› /getvar :</b> ɢᴇᴛ ᴇɴᴠɪʀᴏɴᴍᴇɴᴛ ᴠᴀʀɪᴀʙʟᴇ
<b>›› /restart :</b> ʀᴇsᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ"""

CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", "<b>• ʙʏ @Anime_Lord_Official</b>")
# --------------------------------------------
# Set true if you want Disable your Channel Posts Share button
# --------------------------------------------
BOT_STATS_TEXT = "<b>BOT FUCKTIME</b>\n{uptime}"
USER_REPLY_TEXT = "ʙᴀᴋᴋᴀ ! ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴍʏ ꜱᴇɴᴘᴀɪ!!"

# ==========================(BUY PREMIUM)====================#
OWNER_TAG = os.environ.get("OWNER_TAG", "Aɴɪᴍᴇ Lᴏʀᴅ")
UPI_ID = os.environ.get("UPI_ID", "yourname@upi")  # Replace with your valid UPI ID
QR_PIC = os.environ.get("QR_PIC", "https://telegra.ph/file/3e83c69804826b3cba066.jpg")
SCREENSHOT_URL = os.environ.get("SCREENSHOT_URL", "t.me/mehediyt69")
# --------------------------------------------
# Time and its price
# 7 Days
PRICE1 = os.environ.get("PRICE1", "0 rs")
# 1 Month
PRICE2 = os.environ.get("PRICE2", "60 rs")
# 3 Month
PRICE3 = os.environ.get("PRICE3", "150 rs")
# 6 Month
PRICE4 = os.environ.get("PRICE4", "280 rs")
# 1 Year
PRICE5 = os.environ.get("PRICE5", "550 rs")

# ====================(END)========================#

# Default settings (loaded dynamically in bot.py)
PROTECT_CONTENT = False
HIDE_CAPTION = False
DISABLE_CHANNEL_BUTTON = True
BUTTON_NAME = None
BUTTON_LINK = None

# Function to update settings (used by file_settings.py)
async def update_setting(setting_name, value):
    await db.update_setting(setting_name, value)
    # Update local variables (optional, for immediate use)
    global PROTECT_CONTENT, HIDE_CAPTION, DISABLE_CHANNEL_BUTTON, BUTTON_NAME, BUTTON_LINK
    if setting_name == "PROTECT_CONTENT":
        PROTECT_CONTENT = value
    elif setting_name == "HIDE_CAPTION":
        HIDE_CAPTION = value
    elif setting_name == "DISABLE_CHANNEL_BUTTON":
        DISABLE_CHANNEL_BUTTON = value
    elif setting_name == "BUTTON_NAME":
        BUTTON_NAME = value
    elif setting_name == "BUTTON_LINK":
        BUTTON_LINK = value

# Function to get all settings (used to display in /fsettings)
def get_settings():
    return {
        "PROTECT_CONTENT": PROTECT_CONTENT,
        "HIDE_CAPTION": HIDE_CAPTION,
        "DISABLE_CHANNEL_BUTTON": DISABLE_CHANNEL_BUTTON,
        "BUTTON_NAME": BUTTON_NAME,
        "BUTTON_LINK": BUTTON_LINK
    }

LOG_FILE_NAME = "animelordbot.txt"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            LOG_FILE_NAME,
            maxBytes=50000000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)

# Admin filter to check if user is an admin or owner
async def admin_filter(_, __, message):
    admin_ids = await db.get_all_admins()
    return message.from_user.id in admin_ids or message.from_user.id == OWNER_ID

admin = filters.create(admin_filter)

#
# Copyright (C) 2025 by AnimeLord-Bots@Github, < https://github.com/AnimeLord-Bots >.
#
# This file is part of < https://github.com/AnimeLord-Bots/FileStore > project,
# and is released under the MIT License.
# Please see < https://github.com/AnimeLord-Bots/FileStore/blob/master/LICENSE >
#
# All rights reserved.
#
