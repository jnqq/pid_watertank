#!/usr/bin/env python
import keyboard
from bokeh.plotting import figure, output_file, save
from bokeh.models import BoxAnnotation
from selenium import webdriver
import time
import threading
import PySimpleGUI as sg
sg.theme('DarkAmber')
layout = [ [sg.Text('Enter tank level [%]'), sg.InputText()],
           [sg.Text('Set freeze time [s]'), sg.InputText()],
            [sg.Button('OK'), sg.Button('STOP'), sg.Button('EXIT'), sg.Button('FREEZE')]]

window = sg.Window('Water Tank Control Panel', layout)

x_values = []
y_values = []
t = 0
run = True
flowRatio = 5
OutFlowRatio = 0.5
freeze = 0
driver = webdriver.Firefox()
driver.get(r'file:////home/bart/Documents/python_projects/pid_watertank/index.html')
output_file('index.html')
plot = figure(title = 'test', x_axis_label = 'time [ds]', y_axis_label = 'water level [%]', plot_width=900, plot_height=900)
plot.line(x_values, y_values, line_width= 3)
low_box = BoxAnnotation(top=0, fill_alpha=0.1, fill_color='red')
mid_box = BoxAnnotation(bottom=0, top=100, fill_alpha=0.1, fill_color='green')
high_box = BoxAnnotation(bottom=90, fill_alpha=0.1, fill_color='red')
plot.add_layout(low_box)
plot.add_layout(mid_box)
plot.add_layout(high_box)

class pid(object):
    def __init__(self, Kp=0.1, Ki=0.005, Kd=0.02, Sp = 0, Der=0, Integ=0, Integ_max=100, Integ_min=-100):
        self.Kp = Kp
        self.Kd = Kd
        self.Ki = Ki
        self.SP = Sp
        self.Der = Der
        self.Integ = Integ
        self.Integ_max = Integ_max
        self.Integ_min = Integ_min
        self.error = 0
        self.Pid = 0

    def PID(self, ActVal):
        self.error = self.SP - ActVal
        self.P = self.Kp * self.error
        self.D = self.Kd * (self.error - self.Der)
        self.Der = self.error
        self.Integ = self.Integ + self.error
        if self.Integ > self.Integ_max:
            self.Integ = self.Integ_max
        elif self.Integ < self.Integ_min:
            self.Integ = self.Integ_min
        self.I = self.Integ * self.Ki

        PID = self.P + self.I + self.D
        self.Pid = PID
        return PID


class Tank(object):
    def __init__(self, ATL=0, section=100):
        self.ATL = ATL
        self.section = section


def animate(object):
    global x_values, y_values, t, freeze
    t += 1
    x_values.append(t)
    lev = level(object)
    y_values.append(lev)
    plot.title.text = 'Tank level set: ' + str(pid.SP) + ' [%] ' + '(' + str(y_values[-1]) + ')'
    save(plot)
    time.sleep(freeze)
    freeze = 0
    driver.refresh()

def level(object):
    level = object.ATL
    return level


def flow(object):
    global flowRatio
    if object.ATL > 100:
        flowRatio = 0
    PID = pid.PID(object.ATL)
    object.ATL += flowRatio * PID
    animate(object)


def outflow(object):
    global OutFlowRatio
    if object.ATL == 0:
        OutFlowRatio = 0
    elif object.ATL < 100:
        OutFlowRatio = 0.5
        OutFlowRatio *= 2
        object.ATL -= OutFlowRatio
        print(OutFlowRatio)
    animate(object)

def working(object):
    global run
    while run:
        level(object)
        flow(object)
        #outflow(object)

def win(window):
    global run, freeze
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        if event == 'OK':
            pid.SP = int(values[0])
        if event == 'STOP':
            run = False
        if event == 'EXIT':
            driver.close()
            break
        if event == 'FREEZE':
            freeze = int(values[1])
    window.close()

pid = pid()
tank = Tank()
t1 = threading.Thread(target = working, args = (tank, ))
t2 = threading.Thread(target = win, args = (window, ))
t1.start()
t2.start()
if __name__ == '__main__':
    t1.join()
    t2.join()



