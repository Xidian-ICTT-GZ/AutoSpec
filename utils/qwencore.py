import os, sys, time
import openai
import logging
import httpx
from httpx import HTTPTransport
from typing import List
from openai import OpenAI
from LLM4Veri.src.config_manager import ModelConfig


def num_tokens_from_messages(messages, model="qwen-turbo"):
    return 0


def find_best_reply_content(reply_list):
    best_reply = reply_list[0]
    return best_reply

class BaseChatClass:
    # [修改点 2] 构造函数现在接收一个 ModelConfig 实例
    def __init__(self, config: ModelConfig, conversation_list=[], continuous_talking=True) -> None:
        
        self.config = config

        # [修改点 3] 实例化局部 client，使用 ModelConfig 中的配置
        self.client = OpenAI(
            api_key = config.api_key,
            base_url = config.base_url,
        )
        
        # 初始化对话列表，可以加入一个key为system的字典，有助于形成更加个性化的回答
        self.conversation_list = conversation_list
        self.continuous_talking = continuous_talking
    
    # 打印对话
    def show_conversation(self, msg_list):
        for msg in msg_list:
            if msg['role'] == 'user':
                print(f"\U0001f47b: {msg['content']}\n")
            else:
                print(f"\U0001f47D: {msg['content']}\n")

    # 提示chatgpt
    # [修改点 4] 移除 model 参数，使用 config 中的 model_name
    def get_respone(self, prompt, maxTokens=None, temperature_arg=None, stream_out=False, stop_str=None, n_choices=1):
        
        # [新增点] 从 config 或传入参数中确定实际使用的参数值
        used_model = self.config.model_name
        
        # 优先使用传入参数，否则使用 config 中的值，如果 config 中也没有则使用默认值
        used_maxTokens = maxTokens if maxTokens is not None else self.config.params.get('max_tokens', 8192)
        used_temperature = temperature_arg if temperature_arg is not None else self.config.params.get('temperature', 0.7)
        used_timeout = self.config.params.get('timeout', 60) # 从 config 中获取 timeout
        
        # 下面这一步是把用户的问题也添加到对话列表中，这样下一次问问题的时候就能形成上下文了
        self.conversation_list.append({"role":"user", "content":prompt})
        
        for i in range(3):
                # [修改点 5] 使用 self.client 和从 config 获取的参数
                response = self.client.chat.completions.create(
                    model = used_model,
                    messages = self.conversation_list,
                    max_tokens = used_maxTokens,
                    temperature = used_temperature,
                    timeout = used_timeout, # 增加 timeout 参数
                    frequency_penalty = 0,
                    presence_penalty = 0,
                    top_p = 1,
                    stream = stream_out,
                    stop = stop_str,
                    n = 1,
                )
                break
        logging.info("LLM querying ...\n")
        full_reply_content_list = []

        # use stream of chunks
        if stream_out:
            pass 
        # don't use stream of chunks
        else:
            # get the reply content
            for each_choice in response.choices:
                one_reply_content = each_choice.message.content
                full_reply_content_list.append(one_reply_content)
                logging.info(f"\U0001f47D: {one_reply_content}\n")
            #get the useage of the API
            tokens_usage = response.usage.completion_tokens
            
        # find the best reply
        best_reply_content = find_best_reply_content(full_reply_content_list)
        # 下面这一步是把chatGPT的回答也添加到对话列表中，这样下一次问问题的时候就能形成上下文了
        if self.continuous_talking:
            self.conversation_list.append({"role":"assistant", "content":best_reply_content})

        return full_reply_content_list, tokens_usage