import streamlit as st
from backend import chatbot, retrieve_threads
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage
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

config = {
    'configurable':{
        'thread_id': st.session_state['thread_id']
    },
    'metadata':{
        'thread_id': st.session_state['thread_id']
    },
    'run_name':'chat_turn'
}

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
    
    with st.chat_message("assistant"):
        status_holder = {"box": None}


        def ai_only_stream():
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=config,
                stream_mode="messages",
            ):
                if isinstance(message_chunk, ToolMessage):
                    tool_name = getattr(message_chunk, "name", None) or "tool"
                    status_label = f"🔧 Using `{tool_name}` ..."

                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(
                            status_label,
                            expanded=True,
                        )
                    else:
                        status_holder["box"].update(
                            label=status_label,
                            state="running",
                            expanded=True,
                        )

                elif isinstance(message_chunk, AIMessage):
                    # Stream only text; ignore tool-call chunks
                    if isinstance(message_chunk.content, str) and message_chunk.content:
                        if not message_chunk.tool_calls:
                            yield message_chunk.content

                            if status_holder["box"] is not None:
                                status_holder["box"].update(
                                    label="✅ Tool finished",
                                    state="complete",
                                    expanded=False,
                                )


        ai_message = st.write_stream(ai_only_stream())

        if status_holder["box"] is not None:
            status_holder["box"].update(
                label="✅ Tool finished",
                state="complete",
                expanded=False,
            )    

    st.session_state["message_history"].append(
    {
        "role": "assistant",
        "content": ai_message,
    }
)
