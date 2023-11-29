
import sys, os, math, time, csv, yaml, re
import numpy as np

from openpyxl import Workbook
from openpyxl.chart import (
    ScatterChart,
    Reference,
    Series,
)

import tempfile

from PyQt5.QtCore import QAbstractTableModel

import globalData as gd
from utils import *

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from scipy.interpolate import interp1d, make_interp_spline


from pylatex import Document, Section, Subsection, Command, Tabular, Figure, NewPage, TextColor, VerticalSpace, NewLine
from pylatex.utils import italic, NoEscape


def make_pdf_report():
    """ assume profile available """

    pieces = gd.sessionInfo['Pieces']
    cntrating = [cr for nm, x, cr, tl in pieces]

    # we need a (single) temp dir for intermediates.
    tmpdir = Path(tempfile.gettempdir()) / 'RtcApp'
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

        doc.append(f'Date: {gd.metaData["SessionTime"]}\n')
        r = gd.metaData["Rowers"]
        rwrcnt = gd.sessionInfo['RowerCnt']
        if rwrcnt == 1:
            doc.append('Rowers: ')
            doc.append(f'{r[0][0]} ')
        else:
            doc.append('Rowers from bow: ')
            for i in range(rwrcnt):
                doc.append(f'{r[i][0]}, ')
        doc.append(NewLine())
        doc.append(f'Boattype: {gd.metaData["BoatType"]}\n')
        doc.append(f'Calibration: {gd.metaData["Calibration"]}\n')
        doc.append(f'Misc: {gd.metaData["Misc"]}\n')
        doc.append(f'Powerline: {gd.metaData["PowerLine"]}\n')
        doc.append(f'Venue: {gd.metaData["Venue"]}\n')
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

    # for the plots
    fontP = FontProperties()
    fontP.set_size('xx-small')

    # Second page
    with doc.create(Section(f'Boat report {gd.metaData["CrewName"]}', numbering=False)):

        av = ''
        filt = ''
        if gd.averaging:
            av = 'averaging'
        if gd.filter:
            filt = 'filtered'
        pcs = ['all'] + gd.p_names + ['average']
        doc.append(f'Using piece "{pcs[gd.boatPiece]}": {av} {filt}\n')
        doc.append(VerticalSpace("5pt"))
        doc.append(NewLine())

        sensors = gd.sessionInfo['Header']
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(nrows=2, ncols=2)

        ax1.set_title('Speed')
        ax1.grid(True)
        ax2.set_title('Acceleration')
        ax2.grid(True)
        ax3.set_title('Pitch')
        ax3.grid(True)
        ax4.set_title('Accell-Tempo per Piece')
        ax4.grid(True)

        piece = gd.boatPiece
        if piece == 0:
            for i in range(len(gd.p_names)):
                ax1.plot(gd.norm_arrays[i, :, sensors.index('Speed')], linewidth=0.6, label=gd.p_names[i])
                ax2.plot(gd.norm_arrays[i, :, sensors.index('Accel')], linewidth=0.6, label=gd.p_names[i])
                ax3.plot(gd.norm_arrays[i, :, sensors.index('Pitch Angle')], linewidth=0.6, label=gd.p_names[i])
        elif piece == 7:
            speed = np.zeros(gd.norm_arrays[0, :, 1].shape)
            accel = np.zeros(gd.norm_arrays[0, :, 1].shape)
            pitch = np.zeros(gd.norm_arrays[0, :, 1].shape)
            for i in range(len(gd.p_names)):
                speed += gd.norm_arrays[i, :, sensors.index('Speed')]
                accel += gd.norm_arrays[i, :, sensors.index('Accel')]
                pitch += gd.norm_arrays[i, :, sensors.index('Pitch Angle')]
            ax1.plot(speed/6, linewidth=0.6, label=gd.p_names[i])
            ax2.plot(accel/6, linewidth=0.6, label=gd.p_names[i])
            ax3.plot(pitch/6, linewidth=0.6, label=gd.p_names[i])
        else:
            i = piece - 1
            ax1.plot(gd.norm_arrays[i, :, sensors.index('Speed')], linewidth=0.6, label=gd.p_names[i])
            ax2.plot(gd.norm_arrays[i, :, sensors.index('Accel')], linewidth=0.6, label=gd.p_names[i])
            ax3.plot(gd.norm_arrays[i, :, sensors.index('Pitch Angle')], linewidth=0.6, label=gd.p_names[i])

        pa = []
        for i in range(len(gd.p_names)):
            # accel and tempo per piece
            d, a = gd.prof_data[i]
            pa.append((d['Speed'], cntrating[i][1]))
        pa = list(zip(*pa))
        p = [ 10*x for x in pa[0]]  # ad hoc scaling
        ax4.scatter(list(range(len(gd.p_names))), p, marker='H', color='green')
        ax4.scatter(list(range(len(gd.p_names))), pa[1], marker='H', color='blue')

        ax1.legend(loc='lower right', prop=fontP)
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

        fig = plt.figure()
        fig.subplots_adjust(hspace=0.7)
        gs = fig.add_gridspec(5, 2)
        ax1 = fig.add_subplot(gs[0:3, :])
        ax2 = fig.add_subplot(gs[3:, 0])
        ax3 = fig.add_subplot(gs[3:, 1])

        ax1.set_title('Gate Angle - GateForceX')
        ax1.grid(True)
        ax2.set_title('Stretcher ForceX')
        ax2.grid(True)
        ax3.set_title('Power')
        ax3.grid(True)

        rcnt = gd.sessionInfo['RowerCnt']
        piece = gd.crewPiece
        if piece < len(gd.prof_data):
            # a seperate piece, from the tumbler
            cp = gd.crewPiece
            d, aa = gd.prof_data[cp]

            for r in range(rcnt):
                sns = rowersensors(r)
                if gd.sessionInfo['ScullSweep'] == 'sweep':
                    i = sns['GateAngle']
                    j = sns['GateForceX']
                else:
                    i = sns['P GateAngle']
                    j = sns['P GateForceX']

                # stretchers not always present!
                # k = sns['Stretcher Z']
                # todo: create switch to control working in this case

                ax1.plot(gd.norm_arrays[cp, :, i],
                         gd.norm_arrays[cp, :, j], linewidth=0.6, label=f'R {r+1}')

                #ax2.plot(gd.norm_arrays[gd.crewPiece, :, k], linewidth=0.6, label=f'R {r+1}')
                ax3.plot(aa[0+r], linewidth=0.6, label=f'R {r+1}')

                ax3.plot([gd.gmin[gd.crewPiece]], [0], marker='v', color='b')
                ax3.plot([gd.gmax[gd.crewPiece]], [0], marker='^', color='b')

            # reference curve derived from the stroke
            sns = rowersensors(rcnt-1)
            fmean = d[rcnt-1]['GFEff']
            fmean = 1.15*fmean
            if gd.sessionInfo['ScullSweep'] == 'sweep':
                i = sns['GateAngle']
                j = sns['GateForceX']
            else:
                i = sns['P GateAngle']
                j = sns['P GateForceX']
            minpos = min(gd.norm_arrays[cp, :, i])
            maxpos = max(gd.norm_arrays[cp, :, i])
            minarg = np.argmin(gd.norm_arrays[cp, :, i])
            maxarg = np.argmax(gd.norm_arrays[cp, :, i])
            fmin = gd.norm_arrays[cp, minarg, j]
            fmax = gd.norm_arrays[cp, maxarg, j]
            xstep = (maxpos - minpos)/20
            ystep = (fmin - fmax)/20   # assume fmin > fmax

            if gd.sessionInfo['ScullSweep'] == 'sweep':
                xref = np.array([minpos, minpos+0.4*xstep, minpos+2*xstep, minpos+5*xstep, minpos+7*xstep, minpos+9*xstep, minpos+11*xstep, minpos+14*xstep, minpos+16*xstep, minpos+20*xstep])
                yref = np.array([fmin  , fmin+50,          1.1*fmean,     1.6*fmean,      1.65*fmean,      1.65*fmean,      1.6*fmean,       1.3*fmean,       0.9*fmean,       fmax])
            else:
                xref = np.array([minpos, minpos+0.4*xstep, minpos+2*xstep, minpos+5*xstep, minpos+7*xstep, minpos+9*xstep, minpos+11*xstep, minpos+14*xstep, minpos+16*xstep, minpos+20*xstep])
                yref = np.array([fmin  , fmin+50,          1.1*fmean,     1.6*fmean,      1.65*fmean,      1.65*fmean,      1.6*fmean,       1.3*fmean,       0.9*fmean,       fmax])

            curveref = make_interp_spline(xref, yref)
            xrefnew =  np.linspace(min(xref), max(xref), int(maxpos-minpos))

            ax1.plot(xrefnew, curveref(xrefnew), color='black', linewidth=0.5, linestyle=stippel)
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
                    angle += gd.norm_arrays[p, :, i]
                    force += gd.norm_arrays[p, :, j]
                    # stretcherZ = gd.norm_arrays[p, :, k]
                    d, a = gd.prof_data[p]
                    power += aa[0+r]

                # plot
                #ax1.plot(angle/nmbrpieces, linewidth=0.6, label=f'R {r+1}')
                #ax2.plot(force/nmbrpieces, linewidth=0.6, label=f'R {r+1}')

                ax3.plot(power/nmbrpieces, linewidth=0.6, label=f'R {r+1}')

        ax1.legend(loc='upper right', prop=fontP)
        ax3.legend(loc='upper right', prop=fontP)
        plt.tight_layout()

        # we keep using the same name
        tmpfig = tmpdir / (gd.config['Session'] + '_crew')
        plt.savefig(tmpfig)
        tmpfig = re.sub('\\\\', '/', str(tmpfig))   # for windows
        doc.append(NoEscape(r'\includegraphics[width=1.0\textwidth]{' + f'{tmpfig}'  + r'}'))
        doc.append('\n\n')
        plt.close(fig)

        for i in range(rwrcnt):
            rower = gd.metaData['Rowers'][i][0]
            doc.append(f'Rower {i+1} : {rower}\n')
        
    # Rower pages
    doc.append(NewPage())

    rwrcnt = gd.sessionInfo['RowerCnt']
    fig  = [ None for i in range(rwrcnt)]
    rax1  = [ None for i in range(rwrcnt)]
    sax1  = [ None for i in range(rwrcnt)]

    for rwr in range(rwrcnt):
        pcs = ['all'] + gd.p_names + ['average']
        with doc.create(Section(f'Rower: {gd.metaData["Rowers"][rwr][0]}, using piece "{pcs[gd.rowerPiece[rwr]]}"', numbering=False)):

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

            fig[rwr], ((rax1[rwr])) = plt.subplots(nrows=1, ncols=1)
            rax1[rwr].set_title('GateAngle - GateForceX/Y')
            rax1[rwr].grid(True)

            rsens = rowersensors(rwr)
            piece = gd.rowerPiece[rwr]

            scaleAngle = 10
            if gd.rowerPiece[rwr] == 0:
                # all
                for i in range(len(gd.p_names)):
                    if gd.sessionInfo['ScullSweep'] == 'sweep':
                        # print(f'Make rowerplot for {self.rower}')
                        rax1[rwr].plot(gd.norm_arrays[i, :, rsens['GateAngle']],
                                       gd.norm_arrays[i, :, rsens['GateForceX']], linewidth=0.6, label=f'{gd.p_names[i]}')
                        rax1[rwr].plot(gd.norm_arrays[i, :, rsens['GateAngle']],
                                       gd.norm_arrays[i, :, rsens['GateForceY']], linestyle=(0, (7, 10)), linewidth=0.6, label=f'{gd.p_names[i]}')
                    else:
                        rax1[rwr].plot(gd.norm_arrays[i, :, rsens['P GateAngle']],
                                       gd.norm_arrays[i, :, rsens['P GateForceX']], linewidth=0.6, label=f'{gd.p_names[i]}')
                        rax1[rwr].plot(gd.norm_arrays[i, :, rsens['P GateAngle']],
                                       gd.norm_arrays[i, :, rsens['P GateForceY']], linestyle=(0, (7, 10)), linewidth=0.6, label=f'{gd.p_names[i]}')
            elif gd.rowerPiece[rwr] == 7:
                # average
                angle = np.zeros((100,))
                forceX = np.zeros((100,))
                if gd.sessionInfo['ScullSweep'] == 'sweep':
                    for i in range(len(gd.p_names)):
                        angle += gd.norm_arrays[i, :, rsens['GateAngle']]
                        forceX += gd.norm_arrays[i, :, rsens['GateForceX']]
                        forceY += gd.norm_arrays[i, :, rsens['GateForceY']]
                    rax1[rwr].plot(angle/6, forceX/6, linewidth=0.6, label='FX')
                    rax1[rwr].plot(angle/6, forceY/6, linestyle=(0, (7, 10)), linewidth=0.6, label='FY')
                else:
                    for i in range(len(gd.p_names)):
                        angle += gd.norm_arrays[i, :, rsens['P GateAngle']]
                        forceX += gd.norm_arrays[i, :, rsens['P GateForceX']]
                        forceY += gd.norm_arrays[i, :, rsens['P GateForceY']]
                    rax1[rwr].plot(angle/6, forceX/6, linewidth=0.6, label='FX')
                    rax1[rwr].plot(angle/6, forceY/6, linestyle=(0, (7, 10)), linewidth=0.6, label='FY')
            else:
                rp = gd.rowerPiece[rwr] - 1
                sns = rowersensors(rwr)

                # ad hoc angle x 10. Bettet via (max-min). Scale is for force
                # print(f'Create rowerplot for {self.rower}')
                outboat = [ d for d, e in gd.prof_data]
                ri = [a[rwr] for a in outboat]    # rower info per piece
                fmean = ri[rp]['GFEff']
                fmean = 1.15*fmean
                if gd.sessionInfo['ScullSweep'] == 'sweep':
                    i = sns['GateAngle']
                    j = sns['GateForceX']
                    k = sns['GateForceY']
                else:
                    i = sns['P GateAngle']
                    j = sns['P GateForceX']
                    k = sns['P GateForceY']

                # TESTING referentie curve
                # lengte uit tabel? Voorlopig 100, begin goed zetten
                # scale with avarage force
                minpos = min(gd.norm_arrays[rp, :, i])
                maxpos = max(gd.norm_arrays[rp, :, i])
                minarg = np.argmin(gd.norm_arrays[rp, :, i])
                maxarg = np.argmax(gd.norm_arrays[rp, :, i])
                fmin = gd.norm_arrays[rp, minarg, j]
                fmax = gd.norm_arrays[rp, maxarg, j]
                xstep = (maxpos - minpos)/20
                ystep = (fmin - fmax)/20   # assume fmin > fmax

                if gd.sessionInfo['ScullSweep'] == 'sweep':
                    xref = np.array([minpos, minpos+0.4*xstep, minpos+2*xstep, minpos+5*xstep, minpos+7*xstep, minpos+9*xstep, minpos+11*xstep, minpos+14*xstep, minpos+16*xstep, minpos+20*xstep])
                    yref = np.array([fmin  , fmin+50,          1.05*fmean,     1.6*fmean,      1.65*fmean,      1.65*fmean,      1.6*fmean,       1.3*fmean,       0.9*fmean,       fmax])
                else:
                    xref = np.array([minpos, minpos+0.4*xstep, minpos+2*xstep, minpos+5*xstep, minpos+7*xstep, minpos+9*xstep, minpos+11*xstep, minpos+14*xstep, minpos+16*xstep, minpos+20*xstep])
                    yref = np.array([fmin  , fmin+50,          1.05*fmean,     1.6*fmean,      1.65*fmean,      1.65*fmean,      1.6*fmean,       1.3*fmean,       0.9*fmean,       fmax])

                curveref = make_interp_spline(xref, yref)
                xrefnew =  np.linspace(min(xref), max(xref), int(maxpos-minpos))

                rax1[rwr].plot(gd.norm_arrays[rp, :, i],
                               gd.norm_arrays[rp, :, j], linewidth=0.6, label=f'{gd.p_names[rp]} FX')
                rax1[rwr].plot(gd.norm_arrays[rp, :, i],
                               gd.norm_arrays[rp, :, k], linestyle=stippel, linewidth=0.6, label=f'{gd.p_names[rp]} FY')
                rax1[rwr].plot(xrefnew, curveref(xrefnew), color='black', linewidth=0.5, linestyle=(0, (3, 6)))

            # rax1[rwr].legend(loc='lower right', prop=fontP, bbox_to_anchor=(1.05, 1))
            rax1[rwr].legend(loc='upper right', prop=fontP)
            plt.tight_layout()
            
            tmpfig = tmpdir / (gd.config['Session'] + f'_{rwr}')
            plt.savefig(tmpfig)
            tmpfig = re.sub('\\\\', '/', str(tmpfig))   # for windows
            doc.append(NoEscape(r'\includegraphics[width=0.9\textwidth]{' + f'{tmpfig}'  + r'}'))
            plt.close(fig[rwr])

            if 'StretcherForceX' in sensors:
                doc.append('\n')

                # stretcher plot
                fig[rwr], sax1[rwr] = plt.subplots()
                sax1[rwr].set_title('Stretcher')
                sax1[rwr].grid(True)

                rsens = rowersensors(rwr)
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

                    sax1[rwr].legend(loc='lower right', prop=fontP)
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
            extr.plot(times, gd.view_tr[:, i]*scaley, linewidth=0.6, label=name)
        for i, name, scale in secslist:
            extr.plot(times, gd.view_tr2[:, i]*scaley, linewidth=0.6, label=name, linestyle=stippel)

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

        doc.append(NewLine())
        doc.append(VerticalSpace("10pt"))
        doc.append(f' Piece: {gd.selPiece}')
        if gd.sd_selPiece != '':
            doc.append(NewLine())
            doc.append(VerticalSpace("5pt"))
            doc.append(f'Secondary piece: {gd.sd_selPiece}')

    # generate report
    doc.generate_pdf(reportfile, clean_tex=True)


def make_csv_report():
    """ assume profile available (not used anymore) """

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

    rwrcnt = gd.sessionInfo['RowerCnt']
    for rwr in range(rwrcnt):
        name = gd.metaData['Rowers'][rwr][0]

        ws = wb.create_sheet(title=f"Rower report {name}")
        ws.column_dimensions['A'].width = 30


        ws.append([''])
        ws.append([f'Rower report {name} '])
        ws.append([''])

        rows = gd.rowertablemodel[rwr].rowCount()
        columns = gd.rowertablemodel[rwr].columnCount()

        for r in range(rows):
            row = []
            for j in range(columns):
                index = QAbstractTableModel.index(gd.rowertablemodel[rwr], r, j)
                row.append(str(gd.rowertablemodel[rwr].data(index)))
            ws.append(row)

        # GateAngle - GateForceX/Y data voor deze rower in de spreadsheet
        ws.append([''])
        ws.append(["", "", "Normalized stroke (100 steps) data for each piece."])
        ws.append([''])
        pieces = gd.sessionInfo['Pieces']
        row = ['Piece:']
        for i in range(len(pieces)):
            row.append(f'{gd.p_names[i]}'); row.append(''); row.append('')
        ws.append(row)
        ws.append([''])
        fdata = formatforcedata(rwr)
        row = ['Sensor:']
        for i in range(len(pieces)):
            row.append('Angle')
            row.append('ForceX')
            row.append('ForceY')
        ws.append(row)
        for i in range(100):
            row = fdata[i].tolist()
            row.insert(0, '')
            ws.append(row)
        # evt meteen een chart maken

    #
    wb.save(reportfile.as_posix() + '.xlsx')

    #
    #del wb


def formatforcedata(rwr):
    """ create the array to be embedded in the xlsx file (rower rwr tab)
        in correct format   """

    rsens = rowersensors(rwr)
    pieces = gd.sessionInfo['Pieces']
    farray = np.zeros((3*len(pieces), 100))

    i = 0
    if gd.sessionInfo['ScullSweep'] == 'sweep':
        for p in range(len(pieces)):
            #print(f"ddsds  {p}   {farray[i].shape}   {gd.norm_arrays[p, :, rsens['GateAngle']].shape}  {rsens['GateForceX']}")
            farray[i] = gd.norm_arrays[p, :, rsens['GateAngle']]
            farray[i+1] = gd.norm_arrays[p, :, rsens['GateForceX']]
            farray[i+2] = gd.norm_arrays[p, :, rsens['GateForceY']]
            i = i+3
    else:
        for p in range(len(pieces)):
            #print(f"ddsds  {p}   {farray[i].shape}   {gd.norm_arrays[p, :, rsens['P GateAngle']].shape}  {rsens['P GateForceX']}")
            farray[i] = gd.norm_arrays[p, :, rsens['P GateAngle']]
            farray[i+1] = gd.norm_arrays[p, :, rsens['P GateForceX']]
            farray[i+2] = gd.norm_arrays[p, :, rsens['P GateForceY']]
            i = i+3

    # nu ombouwen voor sheet, dus rij voor rij.
    return farray.transpose()

