import streamlit as st
from backend import chatbot, retrieve_threads
from langchain_core.messages import HumanMessage, AIMessage
import uuid

# *****************************************Utility functions*******************************************

def generate_id():
    thread_id = uuid.uuid4()
    return thread_id

def add_thread(thread_id):
    if thread_id not in st.session_state['thread_history']:
        st.session_state['thread_history'].append(thread_id)

def reset_chat():
    thread_id = generate_id()
    st.session_state['thread_id']=thread_id
    add_thread(thread_id)
    st.session_state['message_history']=[]

def load_messages(thread_id):
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    return state.values.get('messages', [])


if 'thread_history' not in st.session_state:
    st.session_state['thread_history']=retrieve_threads()


if 'message_history' not in st.session_state:
    st.session_state['message_history']=[]

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_id()

add_thread(st.session_state['thread_id'])


for message in st.session_state['message_history'][::]:
    with st.chat_message(message['role']):
        st.text(message['content'])

config = {'configurable':{'thread_id':st.session_state['thread_id']}}

# *****************************************Sidebar*******************************************

st.sidebar.title('Langgraph Chatbot')

if st.sidebar.button('New Chat'):
    reset_chat()

st.sidebar.header('My conversations')
for thread_id in st.session_state['thread_history']:
    if st.sidebar.button(str(thread_id)):
        st.session_state['thread_id']=thread_id
        messages = load_messages(thread_id)

        temp_messages = []

        for message in messages:
            if isinstance(message,HumanMessage):
                role = 'user'
            else:
                role = 'assistant'
            temp_messages.append({'role':role,'content':message.content})

        st.session_state['message_history']=temp_messages

# *****************************************chat UI*******************************************

user_input = st.chat_input()

if user_input:
    with st.chat_message('user'):
        st.session_state['message_history'].append({
            'role':'user',
            'content':user_input
        })
        st.text(user_input)
    with st.chat_message('assistant'):
        ai_msg = st.write_stream( message_chunk.content for message_chunk, metadata in chatbot.stream({
            'messages':[
                HumanMessage(content=user_input)
            ]
        },
        config=config,
        stream_mode='messages'))
        st.session_state['message_history'].append({
    'role':'assistant',
    'content':ai_msg
})