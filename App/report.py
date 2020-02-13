
import sys, os, math, time, csv, yaml, re
import numpy as np

from PyQt5.QtCore import QAbstractTableModel

import globalData as gd
from utils import *

import matplotlib.pyplot as plt

from pylatex import Document, Section, Subsection, Command, Tabular, Figure, NewPage
from pylatex.utils import italic, NoEscape


def make_pdf_report():
    """ assume profile available """
    
    # we need a (single) temp dir for intermediates.
    tmpdir = Path.home() / gd.config['BaseDir'] / 'reports' / 'tmp'
    print(tmpdir)
    if not tmpdir.is_dir():
        tmpdir.mkdir()
    # subdir
    if not reportsDir().is_dir():
        reportsDir().mkdir()
    
    reportfile = reportsDir() / gd.config['Session']

    crewname = gd.sessionInfo['CrewInfo']

    geometry_options = {"top": "5mm", "bottom": "5mm", "right": "5mm", "left": "5mm"}
    doc = Document(documentclass='article', geometry_options=geometry_options, document_options=["12pt"])
    
    #doc.preamble.append(Command('title', f'Report for {crewname}'))
    # doc.preamble.append(Command('date', NoEscape(r'\today')))
    doc.preamble.append(NoEscape(r'\usepackage{graphicx}'))
    #doc.append(NoEscape(r'\maketitle'))

    ##   First page
    with doc.create(Section('Boat report', numbering=False)):
        doc.append(f'Roeiers, info, ..\n')

        # get table from boat report
        rows = gd.boattablemodel.rowCount()
        columns = gd.boattablemodel.columnCount()
        boattab = 'l|' + ''.join(['r' for i in range(columns-1)]) + '|'
        with doc.create(Tabular(boattab)) as table:
            table.add_hline()
            row = []
            for j in range(columns):
                index = QAbstractTableModel.index(gd.boattablemodel, 0, j)
                row.append(str(gd.boattablemodel.data(index)))
            table.add_row(row)
            table.add_hline()

            for i in range(rows):
                row = []
                if i == 0:
                    continue
                for j in range(columns):
                    index = QAbstractTableModel.index(gd.boattablemodel, i, j)
                    row.append(str(gd.boattablemodel.data(index)))
                table.add_row(row)
            table.add_hline()
            

            """

            table.add_empty_row()
            table.add_row((4, 5, 6, 7))
            """
        doc.append('\n')
        
        sensors = gd.sessionInfo['Header']
            
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(nrows=2, ncols=2)
        ax1.set_title('Snelheid')
        ax1.grid(True)
        ax2.set_title('Versnelling')
        ax2.grid(True)
        ax3.set_title('Pitch')
        ax3.grid(True)
        ax4.set_title('Versnelling-Tempo per Piece')
        ax4.grid(True)

        for i in range(len(prof_pcs)):
            ax1.plot(gd.norm_arrays[i, :, sensors.index('Speed')], linewidth=0.5, label=prof_pcs[i])
            ax2.plot(gd.norm_arrays[i, :, sensors.index('Accel')], linewidth=0.5, label=prof_pcs[i])
            ax3.plot(gd.norm_arrays[i, :, sensors.index('Pitch Angle')], linewidth=0.5, label=prof_pcs[i])

        pa = []
        for i in range(len(prof_pcs)):
            # versnelling en tempo per piece
            #  bij de oude software was dit versnelling tegen tempo
            d, a = gd.out[i]
            pa.append((d['Speed'], gd.sessionInfo['PieceCntRating'][i][1]))
        pa = list(zip(*pa))
        p = [ 10*x for x in pa[0]]  # ad hoc schaling, snelheid decimeters/seconde
        ax4.scatter(list(range(6)), p, marker='H', color='green')
        ax4.scatter(list(range(6)), pa[1], marker='H', color='blue')

        ax1.legend(loc='lower right')
        plt.tight_layout()

        tmpfig = tmpdir / gd.config['Session']
        plt.savefig(tmpfig)
        tmpfig = re.sub('\\\\', '/', str(tmpfig))   # for windows, backslash komt op linux normaal niet voor.
        doc.append(NoEscape(r'\includegraphics[width=1.0\textwidth]{' + f'{tmpfig}'  + r'}'))

    ##   Second page
    doc.append(NewPage())
    with doc.create(Section('Crew report', numbering=False)):
        doc.append(f'Piece {prof_pcs[gd.crewPiece]} used.\n')
        # nog af laten hangen van stand in

        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(nrows=2, ncols=2)
        ax1.set_title('Gate Angle')
        ax1.grid(True)
        ax2.set_title('Gate Force')
        ax2.grid(True)
        ax3.set_title('Stretcher Force')
        ax3.grid(True)
        ax4.set_title('Power')
        ax4.grid(True)

        rcnt = gd.sessionInfo['RowerCnt']
        piece = gd.crewPiece
        d, a = gd.out[piece]
        for r in range(rcnt):
            sns = rowersensors(r)
            # print(sns)
            # print(f'Maak crewplot voor {r}')
            if gd.sessionInfo['BoatType'] == 'sweep':
                i = sns['GateAngle']
                j = sns['GateForceX']
            else:
                i = sns['P GateAngle']
                j = sns['P GateForceX']
            # stretchers is er niet altijd!
            # k = sns['Stretcher Z']
                    
            een  = ax1.plot(gd.norm_arrays[piece, :, i], linewidth=0.6, label=f'R {r+1}')
            twee = ax2.plot(gd.norm_arrays[piece, :, j], linewidth=0.6, label=f'R {r+1}')
            # drie = ax3.plot(gd.norm_arrays[piece, :, k], linewidth=0.6, label=prof_pcs[r])

            vier = ax4.plot( a[0+r], linewidth=0.6, label='Power')


        ax1.legend(loc='lower right')
        plt.tight_layout()

        # we keep using the same name
        tmpfig = tmpdir / gd.config['Session']
        plt.savefig(tmpfig)
        tmpfig = re.sub('\\\\', '/', str(tmpfig))   # for windows, backslash komt op linux normaal niet voor.
        doc.append(NoEscape(r'\includegraphics[width=1.0\textwidth]{' + f'{tmpfig}'  + r'}'))

        
    doc.append(NewPage())

    rwrcnt = gd.sessionInfo['RowerCnt']
    rfig  = [ None for i in range(rwrcnt)]
    rax1  = [ None for i in range(rwrcnt)]
    rax2  = [ None for i in range(rwrcnt)]
    rax3  = [ None for i in range(rwrcnt)]
    rax4  = [ None for i in range(rwrcnt)]

    for rwr in range(rwrcnt):
        with doc.create(Section(f'Rower {rwr+1}, using piece {prof_pcs[gd.rowerPiece[rwr]]}', numbering=False)):

            rows = gd.rowertablemodel[rwr].rowCount()
            columns = gd.rowertablemodel[rwr].columnCount()
            rowertab = 'l|' + ''.join(['r' for i in range(columns-1)]) + '|'
            with doc.create(Tabular(rowertab)) as table:
                table.add_hline()
                row = []
                for j in range(columns):
                    index = QAbstractTableModel.index(gd.rowertablemodel[rwr], 0, j)
                    row.append(str(gd.rowertablemodel[rwr].data(index)))
                table.add_row(row)
                table.add_hline()

                for i in range(rows):
                    row = []
                    if i == 0:
                        continue
                    for j in range(columns):
                        index = QAbstractTableModel.index(gd.rowertablemodel[rwr], i, j)
                        row.append(str(gd.rowertablemodel[rwr].data(index)))
                    table.add_row(row)
                table.add_hline()
            doc.append(f'\n')
            
            rfig[rwr], ((rax1[rwr], rax2[rwr]), (rax3[rwr], rax4[rwr])) = plt.subplots(nrows=2, ncols=2)
            rax1[rwr].set_title('GateForce/GateAngle')
            rax1[rwr].grid(True)
            rax2[rwr].set_title('Versnelling')
            rax2[rwr].grid(True)
            rax3[rwr].set_title('GateForce - GateAngle')
            rax3[rwr].grid(True)
            rax4[rwr].set_title('Power')
            rax4[rwr].grid(True)

            rsens = rowersensors(rwr)
            piece = gd.rowerPiece[rwr]
            if gd.sessionInfo['BoatType'] == 'sweep':
                een = rax1[rwr].plot(gd.norm_arrays[piece, :, rsens['GateAngle']]*10, linewidth=0.6, label='GateAngle')
                twee = rax1[rwr].plot(gd.norm_arrays[piece, :, rsens['GateForceX']], linewidth=0.6, label='GateForceX')
                vier = rax3[rwr].plot(gd.norm_arrays[piece, :, rsens['GateAngle']],
                                      gd.norm_arrays[piece, :, rsens['GateForceX']], linewidth=0.6, label='Pitch')
            else:
                een = rax1[rwr].plot(gd.norm_arrays[piece, :, rsens['P GateAngle']]*10, linewidth=0.6, label='GateAngle')
                twee = rax1[rwr].plot(gd.norm_arrays[piece, :, rsens['P GateForceX']], linewidth=0.6, label='GateForceX')
                vier = rax3[rwr].plot(gd.norm_arrays[piece, :, rsens['P GateAngle']],
                                      gd.norm_arrays[piece, :, rsens['P GateForceX']], linewidth=0.6)
            # waarom werkt de legend hier niet?
            drie = rax2[rwr].plot(gd.norm_arrays[piece, :, sensors.index('Accel')], linewidth=0.6, label='Accel')

            d, a = gd.out[piece]
            vijf = rax4[rwr].plot( a[0+rwr], linewidth=0.6, label='Power')

            rax1[rwr].legend(loc='lower right')
            rax2[rwr].legend(loc='lower right')
            rax4[rwr].legend(loc='lower right')
            plt.tight_layout()
            
            tmpfig = tmpdir / (gd.config['Session'] + f'_{rwr}')
            plt.savefig(tmpfig)
            tmpfig = re.sub('\\\\', '/', str(tmpfig))   # for windows, backslash komt op linux normaal niet voor.
            doc.append(NoEscape(r'\includegraphics[width=0.9\textwidth]{' + f'{tmpfig}'  + r'}'))

            if rwr != rwrcnt - 1: 
                doc.append(NewPage())


    # generate the report
    doc.generate_pdf(reportfile, clean_tex=False)
