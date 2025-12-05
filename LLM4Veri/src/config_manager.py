import os
from typing import Dict, Any
import yaml

class ModelConfig:
    """
    封装单一LLM模型配置的容器。
    包含平台、模型名称、API Key 和所有自定义参数。
    """
    def __init__(self, config_id: str, data: Dict[str, Any], resolved_api_key: str = None):
        self.config_id = config_id             # 通常是 model_name
        self.platform = data.get('platform', 'Unknown')
        self.model_name = data.get('model_name', config_id)
        self.base_url = data.get('base_url')
        self.api_key = resolved_api_key        # 已从环境变量中读取到的 Key
        
        # 将所有其他参数存储在 params 字典中，方便 LLMCaller 使用
        self.params = {
            k: v for k, v in data.items() 
            if k not in ['platform', 'model_name', 'api_key_env', 'base_url', 'api_key']
        }

class ConfigLoader:
    """
    负责加载 YAML 文件、解析模型映射和环境变量中的 API Key。
    """
    
    # 静态变量，用于缓存已加载的所有配置
    _templates = {}
    _model_map = {}
    
    @staticmethod
    def _load_all_configs(file_path):
        """私有方法：加载并缓存 YAML 中的所有配置模板和映射。"""
        # 如果已经加载，直接返回
        if ConfigLoader._templates and ConfigLoader._model_map:
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                full_config = yaml.safe_load(f)
                
            ConfigLoader._templates = full_config.get('ConfigTemplates', {})
            ConfigLoader._model_map = full_config.get('ModelMap', {})
        except FileNotFoundError:
            raise FileNotFoundError(f"配置加载错误：找不到文件 '{file_path}'。请确保文件存在于正确路径。")
        except yaml.YAMLError as e:
            raise ValueError(f"配置解析错误：YAML 文件格式不正确。\n错误信息: {e}")

    @staticmethod
    def get_model_config(model_name: str, config_file_path: str = None) -> ModelConfig:
        """
        根据 model_name 查找映射，合并模板，并返回解析后的 ModelConfig 实例。
        这个方法应被 fuzz.py 和 auto_fuzz.py 调用。
        """
        # 1. 健壮地计算配置文件的路径
        if config_file_path is None:
            # 获取当前文件 (config_manager.py) 的绝对路径
            current_file_path = os.path.abspath(__file__)
            # print("Current file path:")
            # print(current_file_path)
            
            # 向上跳两级 (从 src/ 跳到 LLM4Veri/，再跳到 autospec/)
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file_path)))
            # print("Root directory:")
            # print(root_dir)
            # 构造目标路径： autospec/config/models_config.yaml
            config_file_path = os.path.join(root_dir, 'config', 'models_config.yaml')


        # [修正点 2] 确保 ConfigLoader 使用这个计算出的路径
        ConfigLoader._load_all_configs(config_file_path)
        
        # 1. 查找模型映射和覆盖参数
        model_mapping = ConfigLoader._model_map.get(model_name)
        if not model_mapping:
            raise ValueError(f"配置错误：命令行指定的模型名称 '{model_name}' 在 ModelMap 中不存在。")
            
        template_id = model_mapping.get('template_id')
        if not template_id:
             raise ValueError(f"配置错误：模型 '{model_name}' (映射) 未指定 template_id。")

        # 2. 获取配置模板
        template_config = ConfigLoader._templates.get(template_id)
        if not template_config:
            raise ValueError(f"配置错误：Template ID '{template_id}' 在 ConfigTemplates 中不存在。")

        # 3. 合并配置
        final_config_data = template_config.copy() 
        final_config_data['model_name'] = model_name
        
        # 用 ModelMap 中的参数覆盖模板中的参数
        for key, value in model_mapping.items():
            if key != 'template_id':
                final_config_data[key] = value

        # 4. 解析 API Key 凭证
        api_key_env_var = final_config_data.get('api_key_env')
        resolved_key = None
        if api_key_env_var:
            resolved_key = os.getenv(api_key_env_var)
            if resolved_key is None or resolved_key.strip() == "":
                # 提醒用户设置环境变量
                raise ValueError(f"配置错误：模型 '{model_name}' 需要 API Key。环境变量 '{api_key_env_var}' 未设置或为空。")
        
        # 5. 实例化并返回 ModelConfig
        return ModelConfig(
            config_id=model_name,
            data=final_config_data,
            resolved_api_key=resolved_key
        )
        
    @staticmethod
    def get_all_model_configs(config_file_path: str = './LLMVeri/models_config.yaml') -> Dict[str, ModelConfig]:
        """为 auto_fuzz.py 提供便利，返回所有模型名称及其 ModelConfig 实例。"""
        ConfigLoader._load_all_configs(config_file_path)
        
        all_configs = {}
        for model_name in ConfigLoader._model_map.keys():
            try:
                # 递归调用 get_model_config 来加载每个模型的完整配置
                all_configs[model_name] = ConfigLoader.get_model_config(model_name, config_file_path)
            except Exception as e:
                print(f"警告：无法加载模型 '{model_name}' 的配置。错误: {e}")
                continue
        return all_configs