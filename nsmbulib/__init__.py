# 4/3/16
# NSMBULib -- functions useful for NSMBU editors, with C implementations available for speed

# Set up the GTX PIL Plugin if PIL is installed
hasPIL = False
try:
    import PIL
    hasPIL = True
except: pass

if hasPIL:
    from . import _gtxImagePlugin
