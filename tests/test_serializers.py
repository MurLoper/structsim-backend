"""
测试序列化工具
验证 snake_case ↔ camelCase 转换是否正确
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.common.serializers import (
    to_camel_case, to_snake_case,
    dict_keys_to_camel, dict_keys_to_snake,
    serialize_model, serialize_models
)


def test_case_conversion():
    """测试命名转换"""
    print("=" * 60)
    print("🧪 测试命名转换")
    print("=" * 60)
    
    # 测试 snake_case -> camelCase
    test_cases = [
        ('user_name', 'userName'),
        ('created_at', 'createdAt'),
        ('default_sim_type_id', 'defaultSimTypeId'),
        ('id', 'id'),
        ('cpu_core_max', 'cpuCoreMax'),
    ]
    
    print("\n✅ snake_case -> camelCase:")
    for snake, expected_camel in test_cases:
        result = to_camel_case(snake)
        status = "✅" if result == expected_camel else "❌"
        print(f"  {status} {snake:25} -> {result:25} (expected: {expected_camel})")
    
    # 测试 camelCase -> snake_case
    print("\n✅ camelCase -> snake_case:")
    for expected_snake, camel in test_cases:
        result = to_snake_case(camel)
        status = "✅" if result == expected_snake else "❌"
        print(f"  {status} {camel:25} -> {result:25} (expected: {expected_snake})")


def test_dict_conversion():
    """测试字典转换"""
    print("\n" + "=" * 60)
    print("🧪 测试字典转换")
    print("=" * 60)
    
    # 测试简单字典
    snake_dict = {
        'user_id': 1,
        'user_name': 'test',
        'created_at': 1234567890,
        'is_active': True
    }
    
    print("\n原始数据 (snake_case):")
    print(snake_dict)
    
    camel_dict = dict_keys_to_camel(snake_dict)
    print("\n转换后 (camelCase):")
    print(camel_dict)
    
    # 测试嵌套字典
    nested_dict = {
        'user_info': {
            'user_id': 1,
            'user_name': 'test',
            'profile_data': {
                'first_name': 'John',
                'last_name': 'Doe'
            }
        },
        'created_at': 1234567890
    }
    
    print("\n嵌套字典 (snake_case):")
    print(nested_dict)
    
    nested_camel = dict_keys_to_camel(nested_dict)
    print("\n转换后 (camelCase):")
    print(nested_camel)
    
    # 测试列表
    list_data = [
        {'user_id': 1, 'user_name': 'user1'},
        {'user_id': 2, 'user_name': 'user2'}
    ]
    
    print("\n列表数据 (snake_case):")
    print(list_data)
    
    list_camel = dict_keys_to_camel(list_data)
    print("\n转换后 (camelCase):")
    print(list_camel)


def test_model_serialization():
    """测试模型序列化"""
    print("\n" + "=" * 60)
    print("🧪 测试模型序列化")
    print("=" * 60)
    
    from app import create_app, db
    from app.models.config import Project, SimType, ParamDef
    
    app = create_app()
    with app.app_context():
        # 测试 Project 序列化
        project = Project.query.first()
        if project:
            print("\n✅ Project 模型序列化:")
            print("  原始 to_dict():")
            print(f"    {project.to_dict()}")
            
            print("\n  使用 serialize_model():")
            serialized = serialize_model(project)
            print(f"    {serialized}")
        
        # 测试 SimType 序列化
        sim_type = SimType.query.first()
        if sim_type:
            print("\n✅ SimType 模型序列化:")
            print("  原始 to_dict():")
            print(f"    {sim_type.to_dict()}")
            
            print("\n  使用 serialize_model():")
            serialized = serialize_model(sim_type)
            print(f"    {serialized}")
        
        # 测试列表序列化
        params = ParamDef.query.limit(3).all()
        if params:
            print("\n✅ ParamDef 列表序列化:")
            serialized_list = serialize_models(params)
            for i, item in enumerate(serialized_list, 1):
                print(f"  {i}. {item.get('name')}: {item.get('key')}")


if __name__ == '__main__':
    print("\n🚀 开始测试序列化工具\n")
    
    try:
        test_case_conversion()
        test_dict_conversion()
        test_model_serialization()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

