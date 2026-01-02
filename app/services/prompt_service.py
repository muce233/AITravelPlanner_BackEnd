"""提示词管理服务

该模块提供了完整的提示词管理功能,包括:
- 从文件系统加载提示词模板
"""
from typing import Dict, Optional, List
from pathlib import Path
from ..schemas.prompt import (
    PromptTemplate, PromptTemplateType
)

class PromptService:
    """提示词管理服务类
    
    该类负责管理所有的提示词模板，并提供以下核心功能：
    1. 模板管理：加载、获取、重新加载提示词模板
    
    使用示例：
        service = PromptService()
        intent_result = await service.recognize_intent("我想去北京旅游")
        extraction_result = await service.extract_information(intent_result.intent, "我想去北京旅游")
        assembled = service.assemble_prompt(intent_result.intent, extraction_result.extracted_info)
    """

    def __init__(self, prompts_dir: Optional[str] = None):
        """
        初始化提示词服务
        
        构造函数会自动加载指定目录下的所有提示词模板文件（.md格式），
        并根据文件名推断模板的类型和名称。
        
        Args:
            prompts_dir: 提示词文件夹路径，默认为app/prompts
                        如果不提供，则使用相对于当前文件的app/prompts目录
        
        Raises:
            FileNotFoundError: 当指定的提示词文件夹不存在时抛出
        
        Attributes:
            prompts_dir (Path): 提示词文件夹的绝对路径
            _templates (Dict[str, PromptTemplate]): 存储所有加载的提示词模板，键为模板ID
        """
        if prompts_dir is None:
            current_dir = Path(__file__).parent.parent
            prompts_dir = current_dir / "prompts"
        
        self.prompts_dir = Path(prompts_dir)
        self._templates: Dict[str, PromptTemplate] = {}
        self._load_templates()

    def _load_templates(self):
        """从prompts文件夹加载所有提示词模板
        
        该方法会遍历PromptTemplateType枚举的所有值,并尝试加载同名的.md文件。
        
        加载过程:
        1. 检查prompts_dir是否存在,不存在则抛出异常
        2. 遍历PromptTemplateType枚举的所有值
        3. 对于每个枚举值,查找同名的.md文件
        4. 读取文件内容作为模板内容
        5. 创建PromptTemplate对象并存储到_templates字典中
        
        Raises:
            FileNotFoundError: 当prompts_dir目录不存在时
        """
        if not self.prompts_dir.exists():
            raise FileNotFoundError(f"提示词文件夹不存在: {self.prompts_dir}")
        
        # 遍历PromptTemplateType枚举的所有值
        for template_type in PromptTemplateType:
            # 使用枚举值作为文件名(转换为小写)
            template_filename = f"{template_type.value}.md"
            template_file = self.prompts_dir / template_filename
            
            # 检查文件是否存在
            if template_file.exists():
                # 读取文件内容
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_content = f.read()
                
                # 创建PromptTemplate对象
                template = PromptTemplate(
                    template_type=template_type,
                    template_content=template_content
                )
                
                # 存储到字典中
                self._templates[template_type.value] = template

    def reload_templates(self):
        """重新加载提示词模板
        
        当prompts_dir目录下的模板文件被修改或新增后，调用此方法可以重新加载所有模板。
        该方法会先清空已加载的模板，然后重新执行加载流程。
        
        使用场景：
        - 模板文件被修改后需要立即生效
        - 新增了模板文件需要加载
        - 需要刷新模板缓存
        
        Note:
            该方法会清除内存中的所有模板，然后重新从文件系统加载，
            可能会短暂影响性能，建议在必要时调用。
        """
        self._templates.clear()
        self._load_templates()

    def get_template(self, template_type: PromptTemplateType) -> Optional[PromptTemplate]:
        """
        根据类型获取提示词模板
        
        遍历已加载的模板，查找第一个匹配指定类型的模板并返回。
        
        Args:
            template_type: 模板类型，使用PromptTemplateType枚举值
        
        Returns:
            Optional[PromptTemplate]: 找到的第一个匹配类型的PromptTemplate对象，如果不存在则返回None
        
        Note:
            如果有多个相同类型的模板，只返回第一个找到的。
            设计上应该避免有多个相同类型的模板。
        
        Example:
            >>> service = PromptService()
            >>> template = service.get_template_by_type(PromptTemplateType.INTENT_RECOGNITION)
            >>> if template:
            ...     print(f"找到模板: {template.template_type.value}")
        """
        for template in self._templates.values():
            if template.template_type == template_type:
                return template
        return None

    def list_templates(self) -> List[PromptTemplate]:
        """
        列出所有提示词模板
        
        返回当前已加载的所有提示词模板的列表。
        
        Returns:
            List[PromptTemplate]: 包含所有已加载模板的列表
        
        Note:
            返回的是模板列表的副本，修改返回的列表不会影响内部存储。
        
        Example:
            >>> service = PromptService()
            >>> templates = service.list_templates()
            >>> for template in templates:
            ...     print(f"{template.template_type.value}")
        """
        return list(self._templates.values())

    def format_template(self, template_type: PromptTemplateType, **kwargs) -> Optional[str]:
        """
        格式化提示词模板
        
        使用提供的参数对模板进行格式化，替换模板中的占位符。
        使用Python的字符串format方法，支持所有标准的格式化语法。
        
        Args:
            template_type: 模板类型，指定要格式化的模板
            **kwargs: 模板变量，键值对形式提供，用于替换模板中的占位符
        
        Returns:
            Optional[str]: 格式化后的提示词字符串，如果模板不存在则返回None
        
        Raises:
            ValueError: 当提供的kwargs中缺少模板所需的变量时抛出
        
        Example:
            >>> service = PromptService()
            >>> # 假设模板内容为："你好{user}，欢迎使用{app_name}"
            >>> formatted = service.format_template("greeting", user="张三", app_name="旅行助手")
            >>> print(formatted)  # 输出: "你好张三，欢迎使用旅行助手"
        """
        template = self.get_template(template_type)
        if not template:
            return None
        
        try:
            return template.template_content.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"缺少模板变量: {e}")

# 创建全局提示词服务实例
# 该实例在模块加载时自动初始化，用于在整个应用中共享同一个PromptService实例
# 使用单例模式可以避免重复加载模板，提高性能并保持状态一致性
prompt_service = PromptService()
