"""
FreeGenius AI Plugin - search chat records

search and open old chat records

[FUNCTION_CALL]
"""

from freegenius import config, get_or_create_collection, add_vector, query_vectors, showErrors
from freegenius import print1, print2, print3
from pathlib import Path
from chromadb.config import Settings
import os, chromadb, re
from prompt_toolkit import print_formatted_text, HTML

chat_store = os.path.join(config.localStorage, "chats")
Path(chat_store).mkdir(parents=True, exist_ok=True)
chroma_client = chromadb.PersistentClient(chat_store, Settings(anonymized_telemetry=False))


def save_chat_record(timestamp, order, record):
    role = record.get("role", "")
    content = record.get("content", "")
    tool = record.get("tool", "")
    if role and role in ("user", "assistant") and content:
        collection = get_or_create_collection(chroma_client, "chats")
        metadata = {
            "platform": config.llmPlatform,
            "timestamp": timestamp,
            "order": order,
            "role": role,
            "tool": tool,
        }
        add_vector(collection, content, metadata)
config.save_chat_record = save_chat_record

def search_chats(function_args):
    query = function_args.get("query") # required
    print3(f"""Query: {query}""")
    collection = get_or_create_collection(chroma_client, "chats")
    res = query_vectors(collection, query, config.chatRecordClosestMatches)
    config.stopSpinning()
    if res:
        exampleID = ""
        # display search results
        print2(config.divider)
        print(">>> retrieved chat records: ")
        for metadata, document in zip(res["metadatas"][0], res["documents"][0]):
            print1(config.divider)
            print3(f"""Chat ID: {metadata["timestamp"]}""")
            if not exampleID:
                exampleID = metadata["timestamp"]
            print3(f"""Order: {metadata["order"]}""")
            print3(f"""Role: {metadata["role"]}""")
            print3(f"""Content: {document}""")
        print1(config.divider)
        print2("Tips: You can load old chat records by quoting a chat ID or timestamp, e.g.")
        print1(f">>> Load chat records with this ID: {exampleID}")
        print2(config.divider)
    return ""

def load_chats(function_args):

    def validateChatFile(chatFile):
        chatFile = os.path.expanduser(chatFile)
        if os.path.isfile(chatFile):
            isfile = True
        elif re.search("^[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]_[0-9][0-9]_[0-9][0-9]_[0-9][0-9]$", chatFile):
            # match chat id format
            folderPath = os.path.join(config.localStorage, "chats", re.sub("^([0-9]+?\-[0-9]+?)\-.*?$", r"\1", chatFile))
            chatFile = os.path.join(folderPath, f"{chatFile}.txt")
            if os.path.isfile(chatFile):
                isfile = True
            else:
                isfile = False
        else:
            isfile = False
        return (isfile, chatFile)

    config.stopSpinning()
    timestamp = function_args.get("id") # required
    isfile, chatFile = validateChatFile(timestamp)
    if not isfile:
        print3(f"Invalid chat ID / file path: {timestamp}")
        return "[INVALID]"

    print3(f"Loading chat records: {timestamp} ...")

    try:
        with open(chatFile, "r", encoding="utf-8") as fileObj:
            messages = fileObj.read()
        currentMessages = eval(messages)
        if type(currentMessages) == list:
            config.currentMessages = currentMessages
            # display loaded messages
            print("")
            for index, i in enumerate(config.currentMessages):
                role = i.get("role", "")
                content = i.get("content", "")
                if role and role in ("user", "assistant") and content:
                    if role == "user":
                        print_formatted_text(HTML(f"<{config.terminalPromptIndicatorColor1}>>>> </{config.terminalPromptIndicatorColor1}><{config.terminalCommandEntryColor1}>{content}</{config.terminalCommandEntryColor1}>"))
                    else:
                        print1(content)
                    if role == 'assistant' and not index == len(config.currentMessages) - 2:
                        print("")
            return ""
        else:
            print3(f"Failed to load chat records '{timestamp}' due to invalid format!")
    except:
        print3(f"Failed to load chat records: {timestamp}\n")
        showErrors()
    return "[INVALID]"

functionSignature1 = {
    "examples": [
        "search our conversations",
        "search chat records",
        "find in chat history",
    ],
    "name": "search_chats",
    "description": """Search chat records""",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query in detail"
            },
        },
        "required": ["query"]
    }
}

functionSignature2 = {
    "examples": [
        "load chat record",
        "open chat history",
    ],
    "name": "load_chats",
    "description": """Load or open old saved chat records if chat ID / timestamp / file path is given""",
    "parameters": {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "description": "The chat ID or timestamp or a file path"
            },
        },
        "required": ["id"]
    }
}

config.inputSuggestions += ["Search chat records: ", "Load chat records with this ID: ", "Load chat records in this file: "]
config.addFunctionCall(signature=functionSignature1, method=search_chats)
config.addFunctionCall(signature=functionSignature2, method=load_chats)