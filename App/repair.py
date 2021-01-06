
"""
   Repair csv files, e.g. when sensors are incorrectly connected or not calibrated.
   Convert to numpy and repair.

   Alternative: use new colomns to store wrong colums. Not using the first row should distinguish them.

   Directy in libreoffice
       move wrong column far to the right, e.d. in AD
       make AC cells:
         e.g.   =ad3+3.5
       copy over complete column.
       save as csv
       exit libreoffice to remove formulas
       laad csv and copy ac to proper place


welke fouten:
  -verlopen calibratie van de hoeken (zie 3 jan 2020)
      toch niet steeds dezelfde fout
      copieer bakboord naar stuurboord: hoek en kracht

"""
