
import sys, os, math, time, csv, yaml, re
import numpy as np

from openpyxl import Workbook

from PyQt5.QtCore import QAbstractTableModel

import globalData as gd
from utils import *

import matplotlib.pyplot as plt

from pylatex import Document, Section, Subsection, Command, Tabular, Figure, NewPage, TextColor, VerticalSpace, NewLine
from pylatex.utils import italic, NoEscape


def make_pdf_report():
    """ assume profile available """

    pieces = gd.sessionInfo['Pieces']
    cntrating = [cr for nm, x, cr, tl in pieces]

    # we need a (single) temp dir for intermediates.
    tmpdir = Path.home() / gd.config['BaseDir'] / 'reports' / 'tmp'
    if not tmpdir.is_dir():
        tmpdir.mkdir()
    # subdir
    if not reportsDir().is_dir():
        reportsDir().mkdir()

    reportfile = reportsDir() / gd.config['Session']

    crewname = gd.metaData['CrewName']

    geometry_options = {"top": "5mm", "bottom": "5mm", "right": "5mm", "left": "5mm"}
    doc = Document(documentclass='article', geometry_options=geometry_options, document_options=["12pt"])

    doc.preamble.append(NoEscape(r'\usepackage{graphicx}'))

    # see https://doc.qt.io/qt-5/qml-color.html for colors
    doc.append(NoEscape(r'\definecolor{aquamarine}{HTML}{7fffd4}'))
    doc.append(NoEscape(r'\definecolor{gainsboro}{HTML}{dcdcdc}'))

    #   First page
    with doc.create(Section(f'Boat report {gd.metaData["CrewName"]}', numbering=False)):

        doc.append('Rowers: ')
        r = gd.metaData["Rowers"]
        for i in range(gd.sessionInfo['RowerCnt']):
            doc.append(f'{r[i][0]}, ')
        doc.append(NewLine())
        doc.append(f'Boattype: {gd.metaData["BoatType"]}\n')
        doc.append(f'Calibration: {gd.metaData["Calibration"]}\n')
        doc.append(f'Misc: {gd.metaData["Misc"]}\n')
        doc.append(f'Powerline: {gd.metaData["PowerLine"]}\n')
        doc.append(f'Venue: {gd.metaData["Venue"]}\n')
        doc.append(VerticalSpace("5pt"))
        doc.append(NewLine())

        av = ''
        filt = ''
        if gd.averaging:
            av = 'averaging'
        if gd.filter:
            filt = 'filtered'
        pcs = ['all'] + gd.p_names + ['average']
        doc.append(f'Piece "{pcs[gd.boatPiece]}" used: {av} {filt}\n')
        doc.append(VerticalSpace("5pt"))
        doc.append(NewLine())

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
    doc.append(NewPage())

    # Second page
    with doc.create(Section(f'Boat report {gd.metaData["CrewName"]}', numbering=False)):

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
            for i in range(len(gd.p_names)):
                ax1.plot(gd.norm_arrays[i, :, sensors.index('Speed')], linewidth=0.5, label=gd.p_names[i])
                ax2.plot(gd.norm_arrays[i, :, sensors.index('Accel')], linewidth=0.5, label=gd.p_names[i])
                ax3.plot(gd.norm_arrays[i, :, sensors.index('Pitch Angle')], linewidth=0.5, label=gd.p_names[i])
        elif piece == 7:
            speed = np.zeros(gd.norm_arrays[0, :, 1].shape)
            accel = np.zeros(gd.norm_arrays[0, :, 1].shape)
            pitch = np.zeros(gd.norm_arrays[0, :, 1].shape)
            for i in range(len(gd.p_names)):
                speed += gd.norm_arrays[i, :, sensors.index('Speed')]
                accel += gd.norm_arrays[i, :, sensors.index('Accel')]
                pitch += gd.norm_arrays[i, :, sensors.index('Pitch Angle')]
            ax1.plot(speed/6, linewidth=0.5, label=gd.p_names[i])
            ax2.plot(accel/6, linewidth=0.5, label=gd.p_names[i])
            ax3.plot(pitch/6, linewidth=0.5, label=gd.p_names[i])
        else:
            i = piece - 1
            ax1.plot(gd.norm_arrays[i, :, sensors.index('Speed')], linewidth=0.5, label=gd.p_names[i])
            ax2.plot(gd.norm_arrays[i, :, sensors.index('Accel')], linewidth=0.5, label=gd.p_names[i])
            ax3.plot(gd.norm_arrays[i, :, sensors.index('Pitch Angle')], linewidth=0.5, label=gd.p_names[i])

        pa = []
        for i in range(len(gd.p_names)):
            # accel and tempo per piece
            d, a = gd.out[i]
            pa.append((d['Speed'], cntrating[i][1]))
        pa = list(zip(*pa))
        p = [ 10*x for x in pa[0]]  # ad hoc scaling
        ax4.scatter(list(range(len(gd.p_names))), p, marker='H', color='green')
        ax4.scatter(list(range(len(gd.p_names))), pa[1], marker='H', color='blue')

        ax1.legend(loc='lower right')
        plt.tight_layout()

        tmpfig = tmpdir / gd.config['Session']
        plt.savefig(tmpfig)
        tmpfig = re.sub('\\\\', '/', str(tmpfig))   # for windows
        doc.append(NoEscape(r'\includegraphics[width=1.0\textwidth]{' + f'{tmpfig}'  + r'}'))
        plt.close(fig)


    ##   Third page
    doc.append(NewPage())
    with doc.create(Section('Crew report', numbering=False)):
        pcs = gd.p_names + ['average']
        doc.append(f'Piece "{pcs[gd.crewPiece]}" used.\n')

        fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6)) = plt.subplots(nrows=3, ncols=2)
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
                # drie = ax3.plot(gd.norm_arrays[piece, :, k], linewidth=0.5, label=gd.p_names[r])

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
                nmbrpieces = len(gd.p_names)
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
                # self.ax3.plot(stetcherZ/nmbrpieces:, k], linewidth=0.5, label=gd.p_names[r])

                ax4.plot(power/nmbrpieces, linewidth=0.5, label='Power')

        ax1.legend(loc='lower right')
        plt.tight_layout()

        # we keep using the same name
        tmpfig = tmpdir / (gd.config['Session'] + '_crew')
        plt.savefig(tmpfig)
        tmpfig = re.sub('\\\\', '/', str(tmpfig))   # for windows
        doc.append(NoEscape(r'\includegraphics[width=1.0\textwidth]{' + f'{tmpfig}'  + r'}'))
        plt.close(fig)

        
    # Rower pages
    doc.append(NewPage())

    rwrcnt = gd.sessionInfo['RowerCnt']
    fig  = [ None for i in range(rwrcnt)]
    rax1  = [ None for i in range(rwrcnt)]
    rax2  = [ None for i in range(rwrcnt)]
    rax3  = [ None for i in range(rwrcnt)]
    rax4  = [ None for i in range(rwrcnt)]
    sax1  = [ None for i in range(rwrcnt)]

    for rwr in range(rwrcnt):
        pcs = ['all'] + gd.p_names + ['average']
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

            doc.append('\n')

            fig[rwr], ((rax1[rwr], rax2[rwr]), (rax3[rwr], rax4[rwr])) = plt.subplots(nrows=2, ncols=2)
            rax1[rwr].set_title('GateForceX/GateAngle')
            rax1[rwr].grid(True)
            rax2[rwr].set_title('Acceleration')
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
                for i in range(len(gd.p_names)):
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
                    for i in range(len(gd.p_names)):
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
                    for i in range(len(gd.p_names)):
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
            plt.close(fig[rwr])

            doc.append('\n')

            # stretcher plot
            fig[rwr], sax1[rwr] = plt.subplots()
            sax1[rwr].set_title('Stretcher')
            sax1[rwr].grid(True)

            rsens = rowersensors(rwr)
            if 'StretcherForceX' not in sensors:
                sax1[rwr].set_title('No Stretcher sensor')
            else:
                if gd.rowerPiece[rwr] == 0:
                    # all DOEN WE NIET
                    pass
                elif gd.rowerPiece[rwr] == len(gd.p_names) + 1:
                    # average DOEN WE NIET
                    pass
                else: 
                    # a piece (alleen dit)
                    i = gd.rowerPiece[rwr] - 1
                    name, se, nr, sp = pieces[i]
                    sax1[rwr].plot(gd.dataObject[sp[0]:sp[1], rsens['StretcherForceX']], linewidth=0.6, label='StretcherForceX')
                    sax1[rwr].plot(10*gd.dataObject[sp[0]:sp[1], rsens['Stretcher RL']], linewidth=0.6, label='Stretcher RL')
                    sax1[rwr].plot(10*gd.dataObject[sp[0]:sp[1], rsens['Stretcher TB']], linewidth=0.6, label='Stretcher TB')

            sax1[rwr].legend(loc='lower right')
            plt.tight_layout()
            
            tmpfig = tmpdir / (gd.config['Session'] + f'_{rwr}_s')
            plt.savefig(tmpfig)
            tmpfig = re.sub('\\\\', '/', str(tmpfig))   # for windows
            doc.append(NoEscape(r'\includegraphics[width=0.6\textwidth]{' + f'{tmpfig}'  + r'}'))

            plt.close(fig[rwr])

            if rwr != rwrcnt - 1: 
                doc.append(NewPage())

    # Extra page
    if gd.extraplot:
        doc.append(NewPage())

        fig, extr = plt.subplots()
        s2 = gd.config['Session2']
        if s2 == '':
            extr.set_title('Custom plot')
        else:
            extr.set_title(f'Custom plot (second session: {s2})')
        extr.grid(True)
        
        # data from update_plot from View piece, can we do this simpler?
        [strt, end, strttime, center, scalex, slist, secslist] = gd.extrasettings
        times = list(map( lambda x: x/Hz, list(range(gd.view_tr.shape[0]))))

        for i, name, scaley in slist:
            extr.plot(times, gd.view_tr[:, i]*scaley, linewidth=0.5, label=name)
        for i, name, scale in secslist:
            extr.plot(times, gd.view_tr2[:, i]*scaley, linewidth=0.5, label=name, linestyle='--')

        dist = (end - strt)
        xFrom = center - scalex*dist/2
        xTo = center + scalex*dist/2

        extr.set_xlim(xFrom, xTo)
        # start at correct beginvalue
        locs = extr.get_xticks()
        ticks = [item+strttime for item in locs]
        extr.set_xticklabels(ticks)
        extr.legend()
        plt.tight_layout()

        # we keep using the same name
        tmpfig = tmpdir / (gd.config['Session'] + '_extra')
        plt.savefig(tmpfig)
        tmpfig = re.sub('\\\\', '/', str(tmpfig))   # for windows
        doc.append(NoEscape(r'\includegraphics[width=1.0\textwidth]{' + f'{tmpfig}'  + r'}'))
        plt.close(fig)

    # generate report
    doc.generate_pdf(reportfile, clean_tex=True)


def make_csv_report():
    """ assume profile available """

    pieces = gd.sessionInfo['Pieces']
    cntrating = [cr for nm, x, cr, tl in pieces]

    # subdir
    if not reportsDir().is_dir():
        reportsDir().mkdir()

    reportfile = reportsDir() / gd.config['Session']

    crewname = gd.metaData['CrewName']
    misc = gd.metaData['Misc']
    calibration = gd.metaData['Calibration']
    
    # create csv version of the report from the table data
    
    # get table from boat report
    rows = gd.boattablemodel.rowCount()
    columns = gd.boattablemodel.columnCount()

    with open(reportfile.as_posix() + '.csv', mode='w') as report_file:
        report_writer = csv.writer(report_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        report_writer.writerow([crewname])
        report_writer.writerow([misc])
        report_writer.writerow([calibration])
        report_writer.writerow([])
        report_writer.writerow(['Boat report'])
        report_writer.writerow([])
        # welk piece gebruikt erbij

        for i in range(rows):
            row = []
            for j in range(columns):
                index = QAbstractTableModel.index(gd.boattablemodel, i, j)
                row.append(str(gd.boattablemodel.data(index)))
            report_writer.writerow(row)

        rcount = gd.sessionInfo['RowerCnt']
        for i in range(rcount):
            name = gd.metaData['Rowers'][i][0]
            report_writer.writerow([])
            report_writer.writerow([])
            report_writer.writerow([f'Rower report {name}'])
            report_writer.writerow([])
            # welk piece gebruikt erbij

            rows = gd.rowertablemodel[i].rowCount()
            columns = gd.rowertablemodel[i].columnCount()

            for r in range(rows):
                row = []
                for j in range(columns):
                    index = QAbstractTableModel.index(gd.rowertablemodel[i], r, j)
                    row.append(str(gd.rowertablemodel[i].data(index)))
                report_writer.writerow(row)


def make_xlsx_report():
    """ assume profile available """

    pieces = gd.sessionInfo['Pieces']
    cntrating = [cr for nm, x, cr, tl in pieces]

    # subdir
    if not reportsDir().is_dir():
        reportsDir().mkdir()

    reportfile = reportsDir() / gd.config['Session']

    crewname = gd.metaData['CrewName']
    misc = gd.metaData['Misc']
    calibration = gd.metaData['Calibration']
    
    # create xlsx version of the report from the table data
    wb = Workbook()
    ws = wb.active
    ws.title = 'Boat report'

    ws.column_dimensions['A'].width = 30
    # get table from boat report
    rows = gd.boattablemodel.rowCount()
    columns = gd.boattablemodel.columnCount()

    ws.append([''])
    ws.append([f'Boat report for {crewname}'])
    ws.append([f'Calibration value: {calibration}'])
    ws.append([''])
    ws.append([misc])
    ws.append([''])

    for i in range(rows):
        row = []
        for j in range(columns):
            index = QAbstractTableModel.index(gd.boattablemodel, i, j)
            row.append(str(gd.boattablemodel.data(index)))
        ws.append(row)

    rcount = gd.sessionInfo['RowerCnt']
    for i in range(rcount):
        name = gd.metaData['Rowers'][i][0]

        ws = wb.create_sheet(title=f"Rower report {name}")
        ws.column_dimensions['A'].width = 30


        ws.append([''])
        ws.append([f'Rower report {name} '])
        ws.append([''])

        rows = gd.rowertablemodel[i].rowCount()
        columns = gd.rowertablemodel[i].columnCount()

        for r in range(rows):
            row = []
            for j in range(columns):
                index = QAbstractTableModel.index(gd.rowertablemodel[i], r, j)
                row.append(str(gd.rowertablemodel[i].data(index)))
            ws.append(row)

    #
    wb.save(reportfile.as_posix() + '.xlsx')

    #
    #del wb
    
