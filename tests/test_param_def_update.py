"""
测试参数定义更新接口
"""
import requests
import json
import pytest

BASE_URL = "http://localhost:5000/api/v1"


def _request_or_skip(method, url, **kwargs):
    try:
        return requests.request(method, url, timeout=3, **kwargs)
    except requests.RequestException as exc:
        pytest.skip(f"requires a running local backend at {BASE_URL}: {exc}")

def test_update_param_def():
    """测试更新参数定义"""
    
    # 1. 先获取一个参数定义
    print("=" * 60)
    print("1. 获取参数定义列表")
    print("=" * 60)
    response = _request_or_skip("GET", f"{BASE_URL}/config/param-defs")
    print(f"状态码: {response.status_code}")
    data = response.json()
    print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    if not data.get('data') or len(data['data']) == 0:
        print("❌ 没有参数定义，无法测试")
        return
    
    param_def = data['data'][0]
    param_id = param_def['id']
    print(f"\n✅ 选择参数定义 ID: {param_id}")
    print(f"原始数据: {json.dumps(param_def, indent=2, ensure_ascii=False)}")
    
    # 2. 更新参数定义
    print("\n" + "=" * 60)
    print("2. 更新参数定义")
    print("=" * 60)

    update_data = {
        "name": param_def['name'] + "_已更新",
        "minVal": 5.5,
        "maxVal": 99.9,
        "defaultVal": "50",
        "precision": 2,
        "sort": param_def['sort'] + 100
    }

    print(f"更新数据: {json.dumps(update_data, indent=2, ensure_ascii=False)}")
    
    response = _request_or_skip(
        "PUT",
        f"{BASE_URL}/config/param-defs/{param_id}",
        json=update_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\n状态码: {response.status_code}")
    result = response.json()
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # 3. 验证更新结果
    print("\n" + "=" * 60)
    print("3. 验证更新结果")
    print("=" * 60)
    
    if result.get('code') == 0:
        updated_data = result.get('data', {})
        print("\n✅ 更新成功！")
        print("\n字段对比：")
        print(f"  name: {param_def.get('name')} -> {updated_data.get('name')}")
        print(f"  key: {param_def.get('key')} -> {updated_data.get('key')}")
        print(f"  minVal: {param_def.get('minVal')} -> {updated_data.get('minVal')}")
        print(f"  maxVal: {param_def.get('maxVal')} -> {updated_data.get('maxVal')}")
        print(f"  defaultVal: {param_def.get('defaultVal')} -> {updated_data.get('defaultVal')}")
        print(f"  precision: {param_def.get('precision')} -> {updated_data.get('precision')}")
        print(f"  sort: {param_def.get('sort')} -> {updated_data.get('sort')}")
        
        # 检查是否真的更新了
        checks = [
            ("minVal", update_data["minVal"], updated_data.get('minVal')),
            ("maxVal", update_data["maxVal"], updated_data.get('maxVal')),
            ("defaultVal", update_data["defaultVal"], updated_data.get('defaultVal')),
        ]
        
        print("\n验证结果：")
        all_passed = True
        for field, expected, actual in checks:
            if expected == actual:
                print(f"  ✅ {field}: {expected} == {actual}")
            else:
                print(f"  ❌ {field}: 期望 {expected}, 实际 {actual}")
                all_passed = False
        
        if all_passed:
            print("\n🎉 所有字段都正确更新了！")
        else:
            print("\n⚠️ 有字段没有正确更新！")
    else:
        print(f"\n❌ 更新失败: {result.get('msg')}")
    
    # 4. 再次获取验证
    print("\n" + "=" * 60)
    print("4. 重新获取验证")
    print("=" * 60)
    
    response = _request_or_skip("GET", f"{BASE_URL}/config/param-defs/{param_id}")
    print(f"状态码: {response.status_code}")
    result = response.json()
    
    if result.get('code') == 0:
        final_data = result.get('data', {})
        print(f"最终数据: {json.dumps(final_data, indent=2, ensure_ascii=False)}")
        
        print("\n最终验证：")
        checks = [
            ("minVal", update_data["minVal"], final_data.get('minVal')),
            ("maxVal", update_data["maxVal"], final_data.get('maxVal')),
            ("defaultVal", update_data["defaultVal"], final_data.get('defaultVal')),
        ]
        
        all_passed = True
        for field, expected, actual in checks:
            if expected == actual:
                print(f"  ✅ {field}: {expected} == {actual}")
            else:
                print(f"  ❌ {field}: 期望 {expected}, 实际 {actual}")
                all_passed = False
        
        if all_passed:
            print("\n🎉 数据库中的数据也正确了！")
        else:
            print("\n⚠️ 数据库中的数据不正确！")

if __name__ == "__main__":
    try:
        test_update_param_def()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
