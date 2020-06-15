
import sys, os, math, time, csv, yaml, re
import numpy as np

from PyQt5.QtCore import QAbstractTableModel

import globalData as gd
from utils import *

import matplotlib.pyplot as plt

from pylatex import Document, Section, Subsection, Command, Tabular, Figure, NewPage, TextColor
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

    # see https://doc.qt.io/qt-5/qml-color.html for colors
    doc.append(NoEscape(r'\definecolor{aquamarine}{HTML}{7fffd4}'))
    doc.append(NoEscape(r'\definecolor{gainsboro}{HTML}{dcdcdc}'))

    ##   First page
    with doc.create(Section(f'Boat report {gd.sessionInfo["CrewInfo"]}', numbering=False)):
        # doc.append(f'Roeiers, info, ..\n')
        av = ''
        filt = ''
        if gd.averaging:
            av = 'averaging'
        if gd.filter:
            filt = 'filtered'
        pcs = ['all'] + prof_pcs + ['average']
        doc.append(f'Piece "{pcs[gd.boatPiece]}" used: {av} {filt}\n')
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
            table.add_row(row, color='aquamarine')
            table.add_hline()

            cnt = 0
            for i in range(rows):
                row = []
                if i == 0:
                    continue
                for j in range(columns):
                    index = QAbstractTableModel.index(gd.boattablemodel, i, j)
                    row.append(str(gd.boattablemodel.data(index)))
                if cnt%2 == 0:
                    table.add_row(row, color='gainsboro')
                else:
                    table.add_row(row, color='aquamarine')
                cnt += 1
            table.add_hline()
            

            """

            table.add_empty_row()
            table.add_row((4, 5, 6, 7))
            """
        doc.append('\n')
        
        sensors = gd.sessionInfo['Header']
            
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(nrows=2, ncols=2)
        ax1.set_title('Speed')
        ax1.grid(True)
        ax2.set_title('Acceleration')
        ax2.grid(True)
        ax3.set_title('Pitch')
        ax3.grid(True)
        ax4.set_title('Accel-Tempo per Piece')
        ax4.grid(True)

        piece = gd.boatPiece
        if piece == 0:
            for i in range(len(prof_pcs)):
                ax1.plot(gd.norm_arrays[i, :, sensors.index('Speed')], linewidth=0.5, label=prof_pcs[i])
                ax2.plot(gd.norm_arrays[i, :, sensors.index('Accel')], linewidth=0.5, label=prof_pcs[i])
                ax3.plot(gd.norm_arrays[i, :, sensors.index('Pitch Angle')], linewidth=0.5, label=prof_pcs[i])
        elif piece == 7:
            speed = np.zeros(gd.norm_arrays[0, :, 1].shape)
            accel = np.zeros(gd.norm_arrays[0, :, 1].shape)
            pitch = np.zeros(gd.norm_arrays[0, :, 1].shape)
            for i in range(len(prof_pcs)):
                speed += gd.norm_arrays[i, :, sensors.index('Speed')]
                accel += gd.norm_arrays[i, :, sensors.index('Accel')]
                pitch += gd.norm_arrays[i, :, sensors.index('Pitch Angle')]
            ax1.plot(speed/6, linewidth=0.5, label=prof_pcs[i])
            ax2.plot(accel/6, linewidth=0.5, label=prof_pcs[i])
            ax3.plot(pitch/6, linewidth=0.5, label=prof_pcs[i])
        else:
            i = piece - 1
            ax1.plot(gd.norm_arrays[i, :, sensors.index('Speed')], linewidth=0.5, label=prof_pcs[i])
            ax2.plot(gd.norm_arrays[i, :, sensors.index('Accel')], linewidth=0.5, label=prof_pcs[i])
            ax3.plot(gd.norm_arrays[i, :, sensors.index('Pitch Angle')], linewidth=0.5, label=prof_pcs[i])

        pa = []
        for i in range(len(prof_pcs)):
            # accel and tempo per piece
            d, a = gd.out[i]
            pa.append((d['Speed'], gd.sessionInfo['PieceCntRating'][i][1]))
        pa = list(zip(*pa))
        p = [ 10*x for x in pa[0]]  # ad hoc scaling
        ax4.scatter(list(range(6)), p, marker='H', color='green')
        ax4.scatter(list(range(6)), pa[1], marker='H', color='blue')

        ax1.legend(loc='lower right')
        plt.tight_layout()

        tmpfig = tmpdir / gd.config['Session']
        plt.savefig(tmpfig)
        tmpfig = re.sub('\\\\', '/', str(tmpfig))   # for windows
        doc.append(NoEscape(r'\includegraphics[width=1.0\textwidth]{' + f'{tmpfig}'  + r'}'))

    ##   Second page
    doc.append(NewPage())
    with doc.create(Section('Crew report', numbering=False)):
        pcs = prof_pcs + ['average']
        doc.append(f'Piece "{pcs[gd.crewPiece]}" used.\n')

        crewfig, ((ax1, ax2), (ax3, ax4), (ax5, ax6)) = plt.subplots(nrows=3, ncols=2)
        ax1.set_title('Gate Angle')
        ax1.grid(True)
        ax2.set_title('Gate ForceX')
        ax2.grid(True)
        ax3.set_title('Stretcher Force')
        ax3.grid(True)
        ax4.set_title('Power')
        ax4.grid(True)
        ax5.set_title('Power Leg')
        ax5.grid(True)
        ax6.set_title('Power Arm/Trunk')
        ax6.grid(True)

        rcnt = gd.sessionInfo['RowerCnt']
        piece = gd.crewPiece
        if piece < 6:
            d, a = gd.out[piece]
            for r in range(rcnt):
                sns = rowersensors(r)
                # print(f'Make crewplot for {r}')
                if gd.sessionInfo['ScullSweep'] == 'sweep':
                    i = sns['GateAngle']
                    j = sns['GateForceX']
                else:
                    i = sns['P GateAngle']
                    j = sns['P GateForceX']
                # stretchers not always available!
                # k = sns['Stretcher Z']
                    
                een  = ax1.plot(gd.norm_arrays[piece, :, i], linewidth=0.5, label=f'R {r+1}')
                twee = ax2.plot(gd.norm_arrays[piece, :, j], linewidth=0.5, label=f'R {r+1}')
                # drie = ax3.plot(gd.norm_arrays[piece, :, k], linewidth=0.5, label=prof_pcs[r])

                vier = ax4.plot( a[0+r], linewidth=0.5, label='Power')
        else:
            # average
            for r in range(rcnt):
                sns = rowersensors(r)
                if gd.sessionInfo['ScullSweep'] == 'sweep':
                    i = sns['GateAngle']
                    j = sns['GateForceX']
                else:
                    i = sns['P GateAngle']
                    j = sns['P GateForceX']
                # stretchers not always available!
                # k = sns['Stretcher Z']
                    
                # average
                nmbrpieces = len(prof_pcs)
                angle = np.zeros((100,))
                force = np.zeros((100,))
                power = np.zeros((100,))
                for p in range(nmbrpieces):
                    angle  += gd.norm_arrays[p, :, i]
                    force  += gd.norm_arrays[p, :, j]
                    # stretcherZ = gd.norm_arrays[p, :, k]
                    d, a = gd.out[p]
                    power  += a[0+r]

                # plot
                ax1.plot(angle/nmbrpieces, linewidth=0.5, label=f'R {r+1}')
                ax2.plot(force/nmbrpieces, linewidth=0.5, label=f'R {r+1}')
                # self.ax3.plot(stetcherZ/nmbrpieces:, k], linewidth=0.5, label=prof_pcs[r])

                ax4.plot(power/nmbrpieces, linewidth=0.5, label='Power')

        ax1.legend(loc='lower right')
        plt.tight_layout()

        # we keep using the same name
        tmpfig = tmpdir / (gd.config['Session'] + '_crew')
        plt.savefig(tmpfig)
        tmpfig = re.sub('\\\\', '/', str(tmpfig))   # for windows
        doc.append(NoEscape(r'\includegraphics[width=1.0\textwidth]{' + f'{tmpfig}'  + r'}'))

        
    # Rower pages
    doc.append(NewPage())

    rwrcnt = gd.sessionInfo['RowerCnt']
    rfig  = [ None for i in range(rwrcnt)]
    rax1  = [ None for i in range(rwrcnt)]
    rax2  = [ None for i in range(rwrcnt)]
    rax3  = [ None for i in range(rwrcnt)]
    rax4  = [ None for i in range(rwrcnt)]

    for rwr in range(rwrcnt):
        pcs = ['all'] + prof_pcs + ['average']
        with doc.create(Section(f'Rower {rwr+1}, using piece "{pcs[gd.rowerPiece[rwr]]}"', numbering=False)):

            rows = gd.rowertablemodel[rwr].rowCount()
            columns = gd.rowertablemodel[rwr].columnCount()
            rowertab = 'l|' + ''.join(['r' for i in range(columns-1)]) + '|'
            with doc.create(Tabular(rowertab)) as table:
                table.add_hline()
                row = []
                for j in range(columns):
                    index = QAbstractTableModel.index(gd.rowertablemodel[rwr], 0, j)
                    row.append(str(gd.rowertablemodel[rwr].data(index)))
                table.add_row(row, color='aquamarine')
                table.add_hline()

                cnt = 0
                for i in range(rows):
                    row = []
                    if i == 0:
                        continue
                    for j in range(columns):
                        index = QAbstractTableModel.index(gd.rowertablemodel[rwr], i, j)
                        row.append(str(gd.rowertablemodel[rwr].data(index)))
                    if cnt%2 == 0:
                        table.add_row(row, color='gainsboro')
                    else:
                        table.add_row(row, color='aquamarine')
                    cnt += 1
                table.add_hline()
            doc.append(f'\n')
            
            rfig[rwr], ((rax1[rwr], rax2[rwr]), (rax3[rwr], rax4[rwr])) = plt.subplots(nrows=2, ncols=2)
            rax1[rwr].set_title('GateForceX/GateAngle')
            rax1[rwr].grid(True)
            rax2[rwr].set_title('Accelleration')
            rax2[rwr].grid(True)
            rax3[rwr].set_title('GateForceX - GateAngle')
            rax3[rwr].grid(True)
            rax4[rwr].set_title('Power')
            rax4[rwr].grid(True)

            rsens = rowersensors(rwr)
            piece = gd.rowerPiece[rwr]

            scaleAngle = 10
            if gd.rowerPiece[rwr] == 0:
                # all
                for i in range(len(prof_pcs)):
                    if gd.sessionInfo['ScullSweep'] == 'sweep':
                        # print(f'Make rowerplot for {self.rower}')
                        rax1[rwr].plot(gd.norm_arrays[i, :, rsens['GateAngle']]*scaleAngle, linewidth=0.5, label='GateAngle')
                        rax1[rwr].plot(gd.norm_arrays[i, :, rsens['GateForceX']], linewidth=0.5, label='GateForceX')
                        rax3[rwr].plot(gd.norm_arrays[i, :, rsens['GateAngle']],
                                       gd.norm_arrays[i, :, rsens['GateForceX']], linewidth=0.5)
                    else:
                        rax1[rwr].plot(gd.norm_arrays[i, :, rsens['P GateAngle']]*scaleAngle, linewidth=0.5, label='GateAngle')
                        rax1[rwr].plot(gd.norm_arrays[i, :, rsens['P GateForceX']], linewidth=0.5, label='GateForceX')
                        rax3[rwr].plot(gd.norm_arrays[i, :, rsens['P GateAngle']],
                                       gd.norm_arrays[i, :, rsens['P GateForceX']], linewidth=0.5)
                    d, a = gd.out[piece]
                    rax4[rwr].plot( a[0+rwr], linewidth=0.5, label='Power')
                rax2[rwr].plot(gd.norm_arrays[i, :, sensors.index('Accel')], linewidth=0.5, label='Accel')
            elif gd.rowerPiece[rwr] == 7:
                # average
                angle = np.zeros((100,))
                forceX = np.zeros((100,))
                accel = np.zeros((100,))
                power = np.zeros((100,))
                if gd.sessionInfo['ScullSweep'] == 'sweep':
                    for i in range(len(prof_pcs)):
                        angle += gd.norm_arrays[i, :, rsens['GateAngle']]
                        forceX += gd.norm_arrays[i, :, rsens['GateForceX']]
                        accel += gd.norm_arrays[i, :, sensors.index('Accel')]
                        d, a = gd.out[i]
                        power += a[0+rwr]
                    rax1[rwr].plot(scaleAngle*angle/6, linewidth=0.5, label='GateAngle')
                    rax1[rwr].plot(forceX/6, linewidth=0.5, label='GateForceX')
                    rax2[rwr].plot(accel/6, linewidth=0.5, label='Accel')
                    rax3[rwr].plot(angle/6, forceX/6, linewidth=0.5)
                    rax4[rwr].plot(power/6, linewidth=0.5, label='Power')
                else:
                    for i in range(len(prof_pcs)):
                        angle += gd.norm_arrays[i, :, rsens['P GateAngle']]
                        forceX += gd.norm_arrays[i, :, rsens['P GateForceX']]
                        accel += gd.norm_arrays[i, :, sensors.index('Accel')]
                        d, a = gd.out[i]
                        power += a[0+rwr]
                    rax1[rwr].plot(scaleAngle*angle/6, linewidth=0.5, label='P GateAngle')
                    rax1[rwr].plot(forceX/6, linewidth=0.5, label='P GateForceX')
                    rax2[rwr].plot(accel/6, linewidth=0.5, label='Accel')
                    rax3[rwr].plot(angle/6, forceX/6, linewidth=0.5)
                    rax4[rwr].plot(power/6, linewidth=0.5, label='Power')

            else:
                i = gd.rowerPiece[rwr] - 1

                # ad hoc angle x 10. Better via (max-min).
                if gd.sessionInfo['ScullSweep'] == 'sweep':
                    # print(f'Make rowerplot for {self.rower}')
                    rax1[rwr].plot(gd.norm_arrays[i, :, rsens['GateAngle']]*scaleAngle, linewidth=0.5, label='GateAngle')
                    rax1[rwr].plot(gd.norm_arrays[i, :, rsens['GateForceX']], linewidth=0.5, label='GateForceX')
                    rax3[rwr].plot(gd.norm_arrays[i, :, rsens['GateAngle']],
                                   gd.norm_arrays[i, :, rsens['GateForceX']], linewidth=0.5)
                else:
                    rax1[rwr].plot(gd.norm_arrays[i, :, rsens['P GateAngle']]*scaleAngle, linewidth=0.5, label='GateAngle')
                    rax1[rwr].plot(gd.norm_arrays[i, :, rsens['P GateForceX']], linewidth=0.5, label='GateForceX')
                    rax3[rwr].plot(gd.norm_arrays[i, :, rsens['P GateAngle']],
                                   gd.norm_arrays[i, :, rsens['P GateForceX']], linewidth=0.5)
                rax2[rwr].plot(gd.norm_arrays[i, :, sensors.index('Accel')], linewidth=0.5, label='Accel')

                d, a = gd.out[i]
                rax4[rwr].plot( a[0+rwr], linewidth=0.5, label='Power')

            rax1[rwr].legend(loc='lower right')
            rax2[rwr].legend(loc='lower right')
            rax4[rwr].legend(loc='lower right')
            plt.tight_layout()
            
            tmpfig = tmpdir / (gd.config['Session'] + f'_{rwr}')
            plt.savefig(tmpfig)
            tmpfig = re.sub('\\\\', '/', str(tmpfig))   # for windows
            doc.append(NoEscape(r'\includegraphics[width=0.9\textwidth]{' + f'{tmpfig}'  + r'}'))

            if rwr != rwrcnt - 1: 
                doc.append(NewPage())


    # generate report
    doc.generate_pdf(reportfile, clean_tex=True)
