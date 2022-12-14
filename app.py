import os
import base64
import random

import librosa
import numpy as np
import pandas as pd
import panel as pn
import soundfile as sf

from scipy.io import wavfile
from scipy.fft import rfftfreq, rfft, irfft

import scipy.signal

from panel.interact import interact

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Slider, Button, Select, CustomJS, Div
from bokeh.models.formatters import PrintfTickFormatter
from bokeh.layouts import column, row, Spacer

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib import cm
from matplotlib.colors import Normalize

# pn.extension('ipywidgets')


file_input = pn.widgets.FileInput(
    accept=".txt,.csv,.wav", width=200, margin=(30, 0, 10, 10))


modes = pn.widgets.Select(name='modes', options=[
                          'default', 'music', 'vocals'], width=380)


info_msg = pn.pane.Alert("""<h1 style="font-size: 50px; color: #242020;">Upload a file and start mixing <br> <span style="font-size: 30px; color: grey;">&lpar;only *.csv and *.wav files&rpar;</span></h1>""",
                         alert_type="dark", width=1000, height=400, margin=(0, 0, 0, 0), sizing_mode='stretch_width')


input_source = ColumnDataSource(pd.DataFrame())
output_source = ColumnDataSource(pd.DataFrame())
# updated_output_source = ColumnDataSource(pd.DataFrame())

hover_tools = [
    ("(time,amp)", "($x, $y)")
]

input_graph = figure(height=280, width=1000,
                     tools="crosshair,pan,reset,save,wheel_zoom", title="Input Graph", tooltips=hover_tools)

input_graph.line(x="time", y="amp", source=input_source,
                 line_width=3, line_alpha=0.6)

input_graph.visible = False


output_graph = figure(height=280, width=1000,
                      tools="crosshair,pan,reset,save,wheel_zoom", title="Output Graph", tooltips=hover_tools, x_range=input_graph.x_range, y_range=input_graph.y_range)

output_graph.line(x="time", y="amp", source=output_source,
                  line_width=3, line_alpha=0.6, color="firebrick")

output_graph.visible = False

default_sliders_values = [0] * 10
music_sliders_values = [0] * 10
vocals_sliders_values = [0] * 10

# slider1 = Slider(title="20Hz - 40Hz", value=0.0,
#                  start=-20.0, end=20.0, step=0.1, format="@[.] {dB}")


slider1 = pn.widgets.FloatSlider(name="20Hz - 40Hz", value=0.0,
                                 start=-20.0, end=20.0, step=0.1, format=PrintfTickFormatter(format='%.2f dB'))
slider2 = pn.widgets.FloatSlider(name="40Hz - 80Hz", value=0.0,
                                 start=-20.0, end=20.0, step=0.1, format=PrintfTickFormatter(format='%.2f dB'))
slider3 = pn.widgets.FloatSlider(name="80Hz - 160Hz", value=0.0,
                                 start=-20.0, end=20.0, step=0.1, format=PrintfTickFormatter(format='%.2f dB'))
slider4 = pn.widgets.FloatSlider(name="160Hz - 320Hz", value=0.0,
                                 start=-20.0, end=20.0, step=0.1, format=PrintfTickFormatter(format='%.2f dB'))
slider5 = pn.widgets.FloatSlider(name="320Hz - 640Hz", value=0.0,
                                 start=-20.0, end=20.0, step=0.1, format=PrintfTickFormatter(format='%.2f dB'))
slider6 = pn.widgets.FloatSlider(name="640Hz - 1280Hz", value=0.0,
                                 start=-20.0, end=20.0, step=0.1, format=PrintfTickFormatter(format='%.2f dB'))
slider7 = pn.widgets.FloatSlider(name="1280Hz - 2560Hz", value=0.0,
                                 start=-20.0, end=20.0, step=0.1, format=PrintfTickFormatter(format='%.2f dB'))
slider8 = pn.widgets.FloatSlider(name="2560Hz - 5120Hz", value=0.0,
                                 start=-20.0, end=20.0, step=0.1, format=PrintfTickFormatter(format='%.2f dB'))
slider9 = pn.widgets.FloatSlider(name="5120Hz - 10024Hz", value=0.0,
                                 start=-20.0, end=20.0, step=0.1, format=PrintfTickFormatter(format='%.2f dB'))
slider10 = pn.widgets.FloatSlider(name="10024Hz - 20000Hz", value=0.0,
                                  start=-20.0, end=20.0, step=0.1, format=PrintfTickFormatter(format='%.2f dB'))


reset_sliders = pn.widgets.Button(
    name='Reset', button_type='primary', width=380)

toggle_spectrograms = pn.widgets.Toggle(
    name='Show spectrograms', button_type='success', width=380)


input_audio = pn.pane.Audio(name='Input Audio')
input_audio.visible = False

input_audio_label = pn.Row("####Input Audio", margin=(12, 0, 0, 0))
input_audio_label.visible = False


output_audio = pn.pane.Audio(name='Output Audio')
output_audio.visible = False

output_audio_label = pn.Row("####Output Audio", margin=(12, 0, 0, 0))
output_audio_label.visible = False


input_spectrogram_label = pn.Row(
    "#### Input Spectrogram", margin=(0, 0, 0, 50))
output_spectrogram_label = pn.Row(
    "#### Output Spectrogram", margin=(0, 0, 0, 50))


input_spectrogram_label.visible = False
output_spectrogram_label.visible = False

input_spectrogram = pn.pane.Matplotlib(object=Figure(), tight=True)
output_spectrogram = pn.pane.Matplotlib(object=Figure(), tight=True)

input_spectrogram.visible = False
output_spectrogram.visible = False


def activate_sliders(flag):
    if flag == True:
        slider1.disabled = False
        slider2.disabled = False
        slider3.disabled = False
        slider4.disabled = False
        slider5.disabled = False
        slider6.disabled = False
        slider7.disabled = False
        slider8.disabled = False
        slider9.disabled = False
        slider10.disabled = False

        reset_sliders.disabled = False
        toggle_spectrograms.disabled = False

    else:
        slider1.disabled = True
        slider2.disabled = True
        slider3.disabled = True
        slider4.disabled = True
        slider5.disabled = True
        slider6.disabled = True
        slider7.disabled = True
        slider8.disabled = True
        slider9.disabled = True
        slider10.disabled = True

        reset_sliders.disabled = True
        toggle_spectrograms.disabled = True


def flatten_sliders():
    slider1.value = 0
    slider2.value = 0
    slider3.value = 0
    slider4.value = 0
    slider5.value = 0
    slider6.value = 0
    slider7.value = 0
    slider8.value = 0
    slider9.value = 0
    slider10.value = 0


activate_sliders(False)


def file_input_callback(*events):

    flatten_sliders()

    for event in events:
        file_name_array = event.new.split(".")
        type = file_name_array[len(file_name_array) - 1]

    file_handler(type)
    plot_input(type)
    flatten_sliders()


def file_handler(type):

    if type == "wav":
        file_input.save("input.wav")
        file_input.save("output.wav")
    elif type == "csv":
        if os.path.exists("input.csv"):
            os.remove("input.csv")

        if os.path.exists("output.csv"):
            os.remove("output.csv")

        csv_file = open("input.csv", "w")
        csv_file.write(file_input.value.decode("utf-8"))
        csv_file.close()

        csv_file = open("output.csv", "w")
        csv_file.write(file_input.value.decode("utf-8"))
        csv_file.close()

    else:
        print("file type is not compatible")


def graph_visibility(flag):
    if flag == True:
        info_msg.visible = False
        input_graph.visible = True
        input_audio.visible = True
        input_audio_label.visible = True
        output_graph.visible = True
        output_audio.visible = True
        output_audio_label.visible = True

    else:
        info_msg.visible = True
        input_graph.visible = False
        input_audio.visible = False
        input_audio_label.visible = False
        output_graph.visible = False
        output_audio.visible = False
        output_audio_label.visible = False


def trigger_spectrogram(spec):
    current = 0

    if spec == "in":
        current = input_spectrogram.dpi
        random_number = random.randint(143, 144)
        while random_number == current:
            random_number = random.randint(143, 144)
        input_spectrogram.dpi = random_number
    elif spec == "out":
        current = output_spectrogram.dpi
        random_number = random.randint(143, 144)
        while random_number == current:
            random_number = random.randint(143, 144)
        output_spectrogram.dpi = random_number


def plot_input(type):

    if type == "wav":

        fs, data = wavfile.read("input.wav")

        n_samples = len(data)
        time = np.linspace(0, n_samples/fs, num=n_samples)

        df = pd.DataFrame(data={
            "time": time,
            "amp": data
        })

        df.astype(float)

        input_source.data = df
        output_source.data = df

        trigger_spectrogram("in")
        trigger_spectrogram("out")

        input_audio.object = "input.wav"
        output_audio.object = "output.wav"

        activate_sliders(True)
        graph_visibility(True)

    elif type == "csv":
        csv_df = pd.read_csv("input.csv", index_col=False, header=0)
        csv_df.columns = ["time", "amp"]

        csv_df = csv_df.astype(float)

        input_source.data = csv_df
        output_source.data = csv_df

        times = csv_df["time"].values
        n_measurements = len(times)
        timespan_seconds = times[-1] - times[0]
        sample_rate_hz = int(n_measurements / timespan_seconds)

        data = csv_df["amp"].divide(32767).values

        if os.path.exists("input.wav"):
            os.remove("input.wav")

        if os.path.exists("output.wav"):
            os.remove("output.wav")

        sf.write("input.wav", data, sample_rate_hz)
        sf.write("output.wav", data, sample_rate_hz)

        trigger_spectrogram("in")
        trigger_spectrogram("out")

        input_audio.object = "input.wav"
        output_audio.object = "output.wav"

        graph_visibility(True)
        activate_sliders(True)

    else:
        graph_visibility(False)
        activate_sliders(False)


def update_output_audio(*events):

    amp = output_source.data["amp"]
    time = output_source.data["time"]

    n_measurements = len(amp)
    timespan_seconds = time[-1] - time[0]
    fs = int(n_measurements / timespan_seconds)

    data = amp/(32767)

    if os.path.exists("output.wav"):
        os.remove("output.wav")

    sf.write("output.wav", data, fs)

    output_audio.object = data
    output_audio.sample_rate = fs


def test_calc(freq_list, fft_list, low, high, coef):
    start = freq_list.index(low)
    end = freq_list.index(high)
    band = fft_list[start:end + 1]
    updated_band = [coef * i for i in band]
    return updated_band


def default_mode_gain():
    amp = input_source.data["amp"].tolist()
    time = input_source.data["time"]

    n_samples = len(amp)
    timespan_seconds = time[-1] - time[0]

    fs = int(n_samples / timespan_seconds)

    data_fft = rfft(amp).tolist()
    freq = rfftfreq(n=n_samples, d=1.0/fs).tolist()

    for i, value in enumerate(default_sliders_values):

        coef = 10**(value/20)

        if i == 0:
            # adding_gain(19.970472013548132, 40.76164835642017, coef)
            # adding_gain(20, 40, coef)
            start = freq.index(20)
            end = freq.index(40)

            band = data_fft[start:end + 1]
            updated_band = [coef * i for i in band]
            data_fft = data_fft[:start] + updated_band + data_fft[end+1:]

        elif i == 1:
            # adding_gain(41, 80, coef)
            start = freq.index(41)
            end = freq.index(80)

            band = data_fft[start:end + 1]
            updated_band = [coef * i for i in band]
            data_fft = data_fft[:start] + updated_band + data_fft[end+1:]

        elif i == 2:
            # adding_gain(81, 160, coef)
            start = freq.index(81)
            end = freq.index(160)

            band = data_fft[start:end + 1]
            updated_band = [coef * i for i in band]
            data_fft = data_fft[:start] + updated_band + data_fft[end+1:]

        elif i == 3:
            # adding_gain(161, 320, coef)
            start = freq.index(161)
            end = freq.index(320)

            band = data_fft[start:end + 1]
            updated_band = [coef * i for i in band]
            data_fft = data_fft[:start] + updated_band + data_fft[end+1:]

        elif i == 4:
            # adding_gain(321, 640, coef)
            start = freq.index(321)
            end = freq.index(640)

            band = data_fft[start:end + 1]
            updated_band = [coef * i for i in band]
            data_fft = data_fft[:start] + updated_band + data_fft[end+1:]
        elif i == 5:
            # adding_gain(641, 1280, coef)
            start = freq.index(641)
            end = freq.index(1280)

            band = data_fft[start:end + 1]
            updated_band = [coef * i for i in band]
            data_fft = data_fft[:start] + updated_band + data_fft[end+1:]
        elif i == 6:
            # adding_gain(1281, 2560, coef)
            start = freq.index(1281)
            end = freq.index(2560)

            band = data_fft[start:end + 1]
            updated_band = [coef * i for i in band]
            data_fft = data_fft[:start] + updated_band + data_fft[end+1:]
        elif i == 7:
            # adding_gain(2561, 5120, coef)
            start = freq.index(2561)
            end = freq.index(5120)

            band = data_fft[start:end + 1]
            updated_band = [coef * i for i in band]
            data_fft = data_fft[:start] + updated_band + data_fft[end+1:]
        elif i == 8:
            # adding_gain(5121, 10240, coef)
            start = freq.index(5121)
            end = freq.index(10240)

            band = data_fft[start:end + 1]
            updated_band = [coef * i for i in band]
            data_fft = data_fft[:start] + updated_band + data_fft[end+1:]
        elif i == 9:
            # adding_gain(10241, 20000, coef)
            start = freq.index(10241)
            try:
                end = freq.index(20000)

            except ValueError:
                end = freq.index(max(freq))

            if end < start:
                tmp = start
                start = end
                end = tmp

            band = data_fft[start:end + 1]
            updated_band = [coef * i for i in band]
            data_fft = data_fft[:start] + updated_band + data_fft[end+1:]

    data = irfft(data_fft)

    output_source.data = pd.DataFrame(data={
        "time": time,
        "amp": data
    })

    data = data/(32767)

    random_number = random.randint(90, 100)

    while random_number == output_audio.volume:
        random_number = random.randint(90, 100)

    output_audio.volume = random_number

    output_audio.object = "output.wav"


def music_mode_gain():
    amp = input_source.data["amp"].tolist()
    time = input_source.data["time"]

    n_samples = len(amp)
    timespan_seconds = time[-1] - time[0]

    fs = int(n_samples / timespan_seconds)

    data_fft = rfft(amp).tolist()
    freq = rfftfreq(n=n_samples, d=1.0/fs).tolist()

    for i, value in enumerate(music_sliders_values):

        coef = 10**(value/20)

        if i == 0:
            # adding_gain(19.970472013548132, 40.76164835642017, coef)
            # adding_gain(20, 40, coef)
            start = freq.index(20)
            end = freq.index(40)

            band = data_fft[start:end + 1]
            updated_band = [coef * i for i in band]
            data_fft = data_fft[:start] + updated_band + data_fft[end+1:]

        elif i == 1:
            # adding_gain(41, 80, coef)
            start = freq.index(41)
            end = freq.index(80)

            band = data_fft[start:end + 1]
            updated_band = [coef * i for i in band]
            data_fft = data_fft[:start] + updated_band + data_fft[end+1:]

        elif i == 2:
            # adding_gain(81, 160, coef)
            start = freq.index(81)
            end = freq.index(160)

            band = data_fft[start:end + 1]
            updated_band = [coef * i for i in band]
            data_fft = data_fft[:start] + updated_band + data_fft[end+1:]

        elif i == 3:
            # adding_gain(161, 320, coef)
            start = freq.index(161)
            end = freq.index(320)

            band = data_fft[start:end + 1]
            updated_band = [coef * i for i in band]
            data_fft = data_fft[:start] + updated_band + data_fft[end+1:]

        elif i == 4:
            # adding_gain(321, 640, coef)
            start = freq.index(321)
            end = freq.index(640)

            band = data_fft[start:end + 1]
            updated_band = [coef * i for i in band]
            data_fft = data_fft[:start] + updated_band + data_fft[end+1:]
        elif i == 5:
            # adding_gain(641, 1280, coef)
            start = freq.index(641)
            end = freq.index(1280)

            band = data_fft[start:end + 1]
            updated_band = [coef * i for i in band]
            data_fft = data_fft[:start] + updated_band + data_fft[end+1:]
        elif i == 6:
            # adding_gain(1281, 2560, coef)
            start = freq.index(1281)
            end = freq.index(2560)

            band = data_fft[start:end + 1]
            updated_band = [coef * i for i in band]
            data_fft = data_fft[:start] + updated_band + data_fft[end+1:]
        elif i == 7:
            # adding_gain(2561, 5120, coef)
            start = freq.index(2561)
            end = freq.index(5120)

            band = data_fft[start:end + 1]
            updated_band = [coef * i for i in band]
            data_fft = data_fft[:start] + updated_band + data_fft[end+1:]
        elif i == 8:
            # adding_gain(5121, 10240, coef)
            start = freq.index(5121)
            end = freq.index(10240)

            band = data_fft[start:end + 1]
            updated_band = [coef * i for i in band]
            data_fft = data_fft[:start] + updated_band + data_fft[end+1:]
        elif i == 9:
            # adding_gain(10241, 20000, coef)
            start = freq.index(10241)
            try:
                end = freq.index(20000)

            except ValueError:
                end = freq.index(max(freq))

            if end < start:
                tmp = start
                start = end
                end = tmp

            band = data_fft[start:end + 1]
            updated_band = [coef * i for i in band]
            data_fft = data_fft[:start] + updated_band + data_fft[end+1:]

    data = irfft(data_fft)

    output_source.data = pd.DataFrame(data={
        "time": time,
        "amp": data
    })

    data = data/(32767)

    random_number = random.randint(90, 100)

    while random_number == output_audio.volume:
        random_number = random.randint(90, 100)

    output_audio.volume = random_number

    output_audio.object = "output.wav"


def vocals_mode_gain():
    amp = input_source.data["amp"].tolist()
    time = input_source.data["time"]

    n_samples = len(amp)
    timespan_seconds = time[-1] - time[0]

    fs = int(n_samples / timespan_seconds)

    data_fft = rfft(amp).tolist()
    freq = rfftfreq(n=n_samples, d=1.0/fs).tolist()

    for i, value in enumerate(vocals_sliders_values):

        coef = 10**(value/20)

        if i == 0:
            # adding_gain(19.970472013548132, 40.76164835642017, coef)
            # adding_gain(20, 40, coef)
            start = freq.index(20)
            end = freq.index(40)

            band = data_fft[start:end + 1]
            updated_band = [coef * i for i in band]
            data_fft = data_fft[:start] + updated_band + data_fft[end+1:]

        elif i == 1:
            # adding_gain(41, 80, coef)
            start = freq.index(41)
            end = freq.index(80)

            band = data_fft[start:end + 1]
            updated_band = [coef * i for i in band]
            data_fft = data_fft[:start] + updated_band + data_fft[end+1:]

        elif i == 2:
            # adding_gain(81, 160, coef)
            start = freq.index(81)
            end = freq.index(160)

            band = data_fft[start:end + 1]
            updated_band = [coef * i for i in band]
            data_fft = data_fft[:start] + updated_band + data_fft[end+1:]

        elif i == 3:
            # adding_gain(161, 320, coef)
            start = freq.index(161)
            end = freq.index(320)

            band = data_fft[start:end + 1]
            updated_band = [coef * i for i in band]
            data_fft = data_fft[:start] + updated_band + data_fft[end+1:]

        elif i == 4:
            # adding_gain(321, 640, coef)
            start = freq.index(321)
            end = freq.index(640)

            band = data_fft[start:end + 1]
            updated_band = [coef * i for i in band]
            data_fft = data_fft[:start] + updated_band + data_fft[end+1:]
        elif i == 5:
            # adding_gain(641, 1280, coef)
            start = freq.index(641)
            end = freq.index(1280)

            band = data_fft[start:end + 1]
            updated_band = [coef * i for i in band]
            data_fft = data_fft[:start] + updated_band + data_fft[end+1:]
        elif i == 6:
            # adding_gain(1281, 2560, coef)
            start = freq.index(1281)
            end = freq.index(2560)

            band = data_fft[start:end + 1]
            updated_band = [coef * i for i in band]
            data_fft = data_fft[:start] + updated_band + data_fft[end+1:]
        elif i == 7:
            # adding_gain(2561, 5120, coef)
            start = freq.index(2561)
            end = freq.index(5120)

            band = data_fft[start:end + 1]
            updated_band = [coef * i for i in band]
            data_fft = data_fft[:start] + updated_band + data_fft[end+1:]
        elif i == 8:
            # adding_gain(5121, 10240, coef)
            start = freq.index(5121)
            end = freq.index(10240)

            band = data_fft[start:end + 1]
            updated_band = [coef * i for i in band]
            data_fft = data_fft[:start] + updated_band + data_fft[end+1:]
        elif i == 9:
            # adding_gain(10241, 20000, coef)
            start = freq.index(10241)
            try:
                end = freq.index(20000)

            except ValueError:
                end = freq.index(max(freq))

            if end < start:
                tmp = start
                start = end
                end = tmp

            band = data_fft[start:end + 1]
            updated_band = [coef * i for i in band]
            data_fft = data_fft[:start] + updated_band + data_fft[end+1:]

    data = irfft(data_fft)

    output_source.data = pd.DataFrame(data={
        "time": time,
        "amp": data
    })

    data = data/(32767)

    random_number = random.randint(90, 100)

    while random_number == output_audio.volume:
        random_number = random.randint(90, 100)

    output_audio.volume = random_number

    output_audio.object = "output.wav"


def update_data_source():

    current_mode = modes.value

    if current_mode == "default":
        default_mode_gain()
    elif current_mode == "music":
        music_mode_gain()
    elif current_mode == "vocals":
        vocals_mode_gain()

    trigger_spectrogram("out")


def update_sliders_value(*events):
    current_mode = modes.value
    for i, s in enumerate([slider1, slider2, slider3, slider4, slider5, slider6, slider7, slider8, slider9, slider10]):

        if current_mode == "default":
            default_sliders_values[i] = np.round(s.value, 3)
        elif current_mode == "music":
            music_sliders_values[i] = np.round(s.value, 3)
        elif current_mode == "vocals":
            vocals_sliders_values[i] = np.round(s.value, 3)

    update_data_source()


for s in [slider1, slider2, slider3, slider4, slider5, slider6, slider7, slider8, slider9, slider10]:
    s.param.watch(update_sliders_value, "value")
    s.jslink(output_graph, value="source")


def flatten_callback(event):
    flatten_sliders()


def change_mode(*events):
    flatten_sliders()


def toggle_spectrograms_callback(*events):

    # print(toggle_spectrograms.value)

    if toggle_spectrograms.value == True:
        input_spectrogram_label.visible = True
        output_spectrogram_label.visible = True
        input_spectrogram.visible = True
        output_spectrogram.visible = True

    else:
        input_spectrogram_label.visible = False
        output_spectrogram_label.visible = False
        input_spectrogram.visible = False
        output_spectrogram.visible = False


def update_spectrogram(spec):
    if spec == "in":
        data = input_source.data["amp"].tolist()
        time = input_source.data["time"]
    elif spec == "out":
        data = output_source.data["amp"].tolist()
        time = output_source.data["time"]

    n_samples = len(time)
    timespan_seconds = time[-1] - time[0]

    fs = int(n_samples / timespan_seconds)

    fig = Figure()

    ax = fig.subplots()

    fig.supxlabel("time [Second]")
    fig.supylabel("frequency [Hz]")

    _, _, _, im = ax.specgram(data, Fs=fs, NFFT=1024)

    fig.colorbar(im, ax=ax)

    if spec == "in":
        input_spectrogram.object = fig
    elif spec == "out":
        output_spectrogram.object = fig


def update_input_spectrograms(*events):
    update_spectrogram("in")


def update_output_spectrograms(*events):
    update_spectrogram("out")


file_input.param.watch(file_input_callback, "filename")


file_input.jslink(input_audio, value="object")
file_input.jslink(output_audio, value="object")

reset_sliders.on_click(flatten_callback)

modes.param.watch(change_mode, "value")

output_audio.param.watch(update_output_audio, "volume")

toggle_spectrograms.param.watch(toggle_spectrograms_callback, "value")

input_spectrogram.param.watch(update_input_spectrograms, "dpi")
output_spectrogram.param.watch(update_output_spectrograms, "dpi")


in_graph_layout = pn.pane.Bokeh(row(column(
    input_graph)))

out_graph_layout = pn.pane.Bokeh(row(column(
    output_graph)))


in_audio_layout = pn.Row(
    input_audio_label, input_audio, margin=(15, 0, 15, 50))

out_audio_layout = pn.Row(
    output_audio_label, output_audio, margin=(15, 0, 15, 50))


spectrograms_layout = pn.Row(pn.Column(input_spectrogram_label, input_spectrogram), pn.Column(
    output_spectrogram_label, output_spectrogram))

visual_sec = pn.Column(info_msg, in_graph_layout,
                       in_audio_layout, out_graph_layout, out_audio_layout, spectrograms_layout, margin=(15, 0, 0, 0))

# visual_sec.visible = False


sliders = pn.Column(reset_sliders, slider1, slider2, slider3, slider4, slider5,
                    slider6, slider7, slider8, slider9, slider10, toggle_spectrograms, width=400, margin=(0, 0, 0, 5))

app = pn.Row(pn.layout.HSpacer(), visual_sec, pn.layout.HSpacer(),
             pn.Column(file_input, modes, sliders), pn.layout.HSpacer())

app.servable(title="Equalizer")
