import streamlit as st
from backend import chatbot
from langchain.messages import HumanMessage, AIMessage

if 'messages' not in st.session_state:
    st.session_state['messages']=[]

for message in st.session_state['messages']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input()

if user_input:
    with st.chat_message('user'):
        st.session_state['messages'].append({
            'role':'user',
            'content':user_input
        })
        st.text(user_input)
    with st.chat_message('assistant'):
        config = {
            'configurable':{
                'thread_id':1,
            }
        }
        content = chatbot.invoke({
            'messages' :[
                HumanMessage(content=user_input)
            ]
        },config=config)['messages'][-1].content
        st.session_state['messages'].append({
        'role':'assistant',
        'content':content
    })
        st.text(content)