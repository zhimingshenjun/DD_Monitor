"""
异常捕获器
"""
import os, sys, time, datetime, subprocess, logging, traceback, platform
from PyQt5.Qt import *


def uncaughtExceptionHandler(exctype, value, tb):
    logging.error("\n************!!!UNCAUGHT EXCEPTION!!!*********************\n" +
                  ("Type: %s" % exctype) + '\n' +
                  ("Value: %s" % value) + '\n' +
                  ("Traceback:" + '\n') +
                    " ".join(traceback.format_tb(tb)) +
                  "************************************************************\n")
    showFaultDialog(err_type=exctype, err_value=value, tb=tb)


def unraisableExceptionHandler(exc_type,exc_value,exc_traceback,err_msg,object):
    logging.error("\n************!!!UNHANDLEABLE EXCEPTION!!!******************\n" +
                  ("Type: %s" % exc_type) + '\n' +
                  ("Value: %s" % exc_value) + '\n' +
                  ("Message: %s " % err_msg) + '\n' +
                  ("Traceback:" + '\n') +
                    " ".join(traceback.format_tb(exc_traceback)) + '\n' +
                  ("On Object: %s" + object) + '\n' +
                  "************************************************************\n")
    showFaultDialog(err_type=exc_type, err_value=exc_value, tb=exc_traceback)


def thraedingExceptionHandler(exc_type,exc_value,exc_traceback,thread):
    logging.error("\n************!!!UNCAUGHT THREADING EXCEPTION!!!***********\n" +
                  ("Type: %s" % exc_type) + '\n' +
                  ("Value: %s" % exc_value) + '\n' +
                  ("Traceback on thread %s: " % thread + '\n') +
                    " ".join(traceback.format_tb(exc_traceback)) +
                  "************************************************************\n")
    showFaultDialog(err_type=exc_type, err_value=exc_value, tb=exc_traceback)


def loggingSystemInfo():
    systemCmd = ""
    gpuCmd = ""
    if platform.system() == 'Windows':
        systemCmd = r"C:\Windows\System32\systeminfo.exe"
        wmi_exe = r"C:\Windows\System32\wbem\WMIC.exe"
        # cmd 下运行 "wmic PATH win32_VideoController GET /?" 查看可查询的参数列表
        gpu_property_list = "AdapterCompatibility, Caption, DeviceID, DriverDate, DriverVersion, VideoModeDescription"
        gpuCmd = f"{wmi_exe} PATH win32_VideoController GET {gpu_property_list} /FORMAT:list"
    elif platform.system() == 'Darwin':
        systemCmd = "/usr/sbin/system_profiler SPHardwareDataType"
        gpuCmd = "/usr/sbin/system_profiler SPDisplaysDataType"
    elif platform.system() == 'Linux':
        systemCmd = "/usr/bin/lscpu"
        gpuCmd = "/usr/bin/lspci"

    systemInfoProcess = subprocess.Popen(systemCmd, shell=True, stdout=subprocess.PIPE,universal_newlines=True)
    systemInfoProcessReturn = systemInfoProcess.stdout.read()
    gpuInfoProcess = subprocess.Popen(gpuCmd, shell=True, stdout=subprocess.PIPE, universal_newlines=True)
    gpuInfoProcessReturn = gpuInfoProcess.stdout.read()

    if platform.system() == 'Windows':
        gpuInfoProcessReturn = gpuInfoProcessReturn.strip()
        gpuInfoProcessReturn = gpuInfoProcessReturn.replace("\n\n", "\n")

    logging.info(f"系统信息: \n{systemInfoProcessReturn}")
    logging.info(f"GPU信息: \n{gpuInfoProcessReturn}")


def showFaultDialog(err_type, err_value, tb):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setText("不好，出现了一个问题: %s" % err_type)
    msg.setInformativeText("运行中出现了%s故障,请到logs文件夹中找到log-%s.txt并上报。" % (err_value, datetime.datetime.today().strftime('%Y-%m-%d')))
    msg.setWindowTitle("DD监控室出现了问题")
    msg.setDetailedText("Traceback:\n%s" % (" ".join(traceback.format_tb(tb))))
    msg.setStandardButtons(QMessageBox.Ok)
    msg.exec_()
