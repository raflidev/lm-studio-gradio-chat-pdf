import gradio as gr
import pandas as pd
import numpy as np
import fitz #PyMuPDF
from openai import OpenAI

client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

history = []

def get_completion(input):
    message = {"role": "user", "content": input}
    _history = history+[message]
    completion = client.chat.completions.create(
        model="local-model",
        messages=_history,
        temperature=0.7,
        stream=True,
    )
    return completion

def wrapper_chat_history(chat_history, history):
    chat_history = history[1:]
    return chat_history

def chatbot_update():
    global data_all
    data_all.at[iterasi, 'Chatbot'] = history[-1]["content"]
    return data_all

def converse(message, chat_history):
    response = get_completion(input=message)
    user_msg = {"role": "user", "content": message}
    history.append(user_msg)
    ai_msg = {"role": "assistant", "content": ""}
    history.append(ai_msg)
    partial_message = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            _tkn = chunk.choices[0].delta.content
            partial_message = partial_message + _tkn
            history[-1]["content"] += _tkn
            chat_history = wrapper_chat_history(chat_history, history)
            yield partial_message

def read_pdf(file):
    with fitz.open(file.name) as doc:
        text = ""
        for page in doc:
            text += page.get_text()
    if(text != ""):
        history.append({"role": "user", "content": text})
    return text

# Fungsi chatbot sederhana
def chatbot(input_text):
    responses = {
        "hi": "Hello!",
        "apa kabar": "Saya baik, terima kasih!",
        "siapa namamu": "Saya adalah chatbot.",
    }
    response = responses.get(input_text.lower(), "Maaf, saya tidak mengerti.")
    return response

def chatbot2(input_text):
    responses = {
        "hi": "Hello!",
        "apa kabar": "Saya baik, terima kasih!",
        "siapa namamu": "Saya adalah chatbot.",
    }
    response = responses.get(input_text.lower(), "Maaf, saya tidak mengerti.")
    return response

data  = pd.DataFrame()
data2 = pd.DataFrame()
data_all = pd.DataFrame({
    'Konteks': [''],
    'Pertanyaan': [''],
    'Chatbot': [''],
    'Catatan': [''],
    'Relevansi': [''],
})
iterasi = 0

def chatbot_response(history, input_text):
    response = chatbot(input_text)
    history.append((input_text, response))
    return history, ""

def chatbot_response2(history, input_text):
    response = chatbot(input_text)
    history.append((input_text, response))
    return history, ""

def place(evt: gr.SelectData):
    global data_all
    data_all.at[iterasi, 'Konteks'] = data['Konteks'].values[evt.index[0]]
    return data['Konteks'].values[evt.index[0]], data_all

def place2(evt: gr.SelectData):
    global data_all
    data_all.at[iterasi, 'Pertanyaan'] = data2['Pertanyaan'].values[evt.index[0]]
    return data2['Pertanyaan'].values[evt.index[0]], data_all

def read_kontek(file):
    df = pd.read_csv(file.name)
    data["Konteks"] = df["Konteks"]
    return df

def read_pertanyaan(file):
    df = pd.read_csv(file.name)
    data2["Pertanyaan"] = df["Pertanyaan"]
    return df

def catatan_user(text):
    global data_all
    data_all.at[iterasi, 'Catatan'] = text
    return data_all

def radio_user(text):
    global data_all
    data_all.at[iterasi, 'Relevansi'] = text
    return data_all

def next_row():
    global iterasi
    iterasi += 1
    return f"Iterasi ke-{iterasi+1}"

data_all_output = gr.DataFrame(data_all, label="Konteks", headers=["Konteks", "Pertanyaan", "Chatbot", "Catatan", "Revelansi"], datatype=['str'], row_count=5, col_count=(5, "fixed"))

with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column(scale=1):
            with gr.Row():
                    df_input = gr.DataFrame(data, label="Daftar Konteks", headers=["Konteks"], datatype=['str'], row_count=5, col_count=(1, "fixed"))
                    text_output = gr.Textbox(show_label=False)
                    df_input.select(place, None, outputs=[text_output, data_all_output])
            with gr.Row():
                    pdf_konteks = gr.File(label="Unggah Dokumen Konteks", type="filepath")
                    pdf_konteks.change(read_kontek, pdf_konteks, df_input)

        with gr.Column(scale=1):
            with gr.Row():
                df_input2 = gr.DataFrame(data2, label="Standar Pertanyaan", headers=["Pertanyaan"], datatype=['str'], row_count=5, col_count=(1, "fixed"))
                text_output2 = gr.Textbox(show_label=False)
                df_input2.select(place2, None, outputs=[text_output2, data_all_output])
            with gr.Row():
                pdf_pertanyaan = gr.File(label="Unggah Dokumen Pertanyaan", type="filepath")
                pdf_pertanyaan.change(read_pertanyaan, pdf_pertanyaan, df_input2)

        with gr.Column(scale=2):
            gr.ChatInterface(fn=converse)
        with gr.Column(scale=1):
            text_user = gr.Textbox(label="Catatan user terhadap model", lines=5, placeholder="Masukkan catatan user terhadap model")
            text_user.change(catatan_user, text_user, data_all_output)

            text_radio = gr.Radio(["Sangat relevan (*****)", "Relevan (****)", "Biasa saja (***)" ,"Tidak Relevan (**)", "Sangat tidak relevan (*)"], label="Relevansi model", info="Penilaian Relevansi user terhadap model")
            text_radio.change(radio_user, text_radio, data_all_output)

            data_all_output.render()
            
            label_next = gr.Label("Iterasi ke-1")
            button_next = gr.Button(value="Next Row (Lakukan jika sudah di step terakhir)")
            button_next.click(next_row, None, label_next)

        with gr.Row():
            pdf_input = gr.File(label="Unggah PDF", type="filepath")
            pdf_output = gr.Textbox(label="Isi PDF")
            pdf_input.change(read_pdf, pdf_input, pdf_output)

# Jalankan Gradio
demo.launch()
