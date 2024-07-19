import os
import sys
import atexit

####A basic function to save lines of data
def save(p,data):
    try:
        (list,dict,tuple).index(type(data)) # Verify data is a List, Dictionary, or Tuple
    except ValueError:
        sys.exit("Error saving data: The data variable must be iterable (e.g., a List). Got %s instead.\nShutting Down..." % str(type(data)))
    
    if save.tofile==None:
        #outfile=dialog.AskFileForSave("Where do you want to save your results?",savedFileName='combined_results.xls',defaultLocation=os.path._getfullpathname('.'))
        outfile="%s.xls" % p
        if outfile!=None and outfile!='':
            try:
                ('.xls','.tab').index(os.path.splitext(outfile)[1])
            except:
                outfile=outfile+'.xls'
            try:
                save.tofile=open(outfile,'w')   # Try to open the output file, and assign the file handle to the save function's persistent .tofile attribute
            except IOError:
                sys.exit("Error saving data: Couldn't open %s for writing.\nShutting down..." % outfile)
            try:
                save(save.OUT_HEADER)
            except:
                pass # There probably just isn't an OUT_HEADER specified and I can accept that.
        else:
            sys.exit("No results file selected.\nShutting down...")
    save.tofile.write('\t'.join(map(str,data))+'\n')
    save.tofile.flush()
# I can add attributes to any object I create, any time I want. The save() function is a function object I just created, so...
save.tofile=None    # This line permanently attaches a .tofile attribute to the save function I defined. It will be persistent and available to all calls to save().
# I could have just used a global variable instead of attaching an attribute to save(), like I did with OUT_HEADER, but then I couldn't use that name elsewhere if I wanted to, so in some sense this is better.
save.OUT_HEADER=None

####A basic function to set the OUT_HEADER attribute of the save() function
def setHeader(header):
    worked=True
    if type(header)==str:
        if header.find(','):
            save.OUT_HEADER=header.split(',')
        elif header.find(' '):
            save.OUT_HEADER=header.split(' ')
        elif header.find('\t'):
            save.OUT_HEADER=header.split('\t')
        else:
            save.OUT_HEADER=(header)
            print("\nWarning: The header appears to contain only one item and may be invalid.\n")
    else:
        try:
            (list,dict,tuple).index(type(header))
            save.OUT_HEADER=header
        except:
            worked=False
    
    return worked

@atexit.register
def _quit():
    if save.tofile!=None:
        print("Closing output file...")
        save.tofile.close()
        save.tofile=None


if __name__=='__main__':
    save(('test','data','output'))
    save(('this','is','line',2))
