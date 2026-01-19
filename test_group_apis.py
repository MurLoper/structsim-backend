"""
测试组合配置 API
测试参数组合和工况输出组合的管理接口
"""

import requests
import json
import random
import string

BASE_URL = "http://localhost:5000/api/v1"

def random_code(prefix="TEST", length=6):
    """生成随机编码"""
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    return f"{prefix}_{suffix}"

def test_api(method, endpoint, data=None, description=""):
    """测试 API 接口"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n{'='*60}")
    print(f"测试: {description}")
    print(f"方法: {method} {endpoint}")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code < 400:
            result = response.json()
            print(f"✓ 成功")
            if 'data' in result:
                print(f"返回数据: {json.dumps(result['data'], ensure_ascii=False, indent=2)[:300]}...")
            return result.get('data')
        else:
            print(f"✗ 失败: {response.text[:500]}")
            return None
            
    except Exception as e:
        print(f"✗ 异常: {e}")
        return None

def test_group_config_apis():
    """测试组合配置 API"""
    
    print("\n" + "="*60)
    print("开始测试组合配置 API")
    print("="*60)
    
    # 1. 测试参数组合 API
    print("\n\n【1. 参数组合管理 API】")
    
    # 1.1 获取参数组合列表
    param_groups = test_api("GET", "/param-groups", description="获取参数组合列表")
    
    # 1.2 创建参数组合
    new_param_group = test_api("POST", "/param-groups",
                               data={
                                   "name": "测试参数组合",
                                   "code": random_code("PG"),
                                   "description": "这是测试参数组合",
                                   "sort": 100
                               },
                               description="创建参数组合")
    
    if new_param_group:
        group_id = new_param_group.get('id')
        
        # 1.3 更新参数组合
        test_api("PUT", f"/param-groups/{group_id}",
                data={"name": "测试参数组合（已更新）", "description": "更新后的描述"},
                description="更新参数组合")
        
        # 1.4 获取组合中的参数
        test_api("GET", f"/param-groups/{group_id}/params",
                description="获取组合中的参数")
        
        # 1.5 添加参数到组合（需要先获取一个参数ID）
        param_defs = test_api("GET", "/config/param-defs", description="获取参数定义列表")
        if param_defs and len(param_defs) > 0:
            param_id = param_defs[0]['id']
            test_api("POST", f"/param-groups/{group_id}/params",
                    data={"paramDefId": param_id, "sort": 10},
                    description=f"添加参数 {param_id} 到组合")
            
            # 1.6 再次获取组合中的参数
            params_in_group = test_api("GET", f"/param-groups/{group_id}/params",
                                      description="获取组合中的参数（添加后）")
            
            # 1.7 从组合中移除参数
            if params_in_group and len(params_in_group) > 0:
                test_api("DELETE", f"/param-groups/{group_id}/params/{param_id}",
                        description=f"从组合中移除参数 {param_id}")
        
        # 1.8 删除参数组合
        test_api("DELETE", f"/param-groups/{group_id}",
                description="删除参数组合")
    
    # 2. 测试工况输出组合 API
    print("\n\n【2. 工况输出组合管理 API】")
    
    # 2.1 获取工况输出组合列表
    cond_out_groups = test_api("GET", "/cond-out-groups", description="获取工况输出组合列表")
    
    # 2.2 创建工况输出组合
    new_cond_out_group = test_api("POST", "/cond-out-groups",
                                  data={
                                      "name": "测试工况输出组合",
                                      "code": random_code("COG"),
                                      "description": "这是测试工况输出组合",
                                      "sort": 100
                                  },
                                  description="创建工况输出组合")
    
    if new_cond_out_group:
        group_id = new_cond_out_group.get('id')
        
        # 2.3 更新工况输出组合
        test_api("PUT", f"/cond-out-groups/{group_id}",
                data={"name": "测试工况输出组合（已更新）"},
                description="更新工况输出组合")
        
        # 2.4 获取组合中的工况
        test_api("GET", f"/cond-out-groups/{group_id}/conditions",
                description="获取组合中的工况")
        
        # 2.5 添加工况到组合
        condition_defs = test_api("GET", "/config/condition-defs", description="获取工况定义列表")
        if condition_defs and len(condition_defs) > 0:
            condition_id = condition_defs[0]['id']
            test_api("POST", f"/cond-out-groups/{group_id}/conditions",
                    data={"conditionDefId": condition_id, "sort": 10},
                    description=f"添加工况 {condition_id} 到组合")
            
            # 2.6 从组合中移除工况
            test_api("DELETE", f"/cond-out-groups/{group_id}/conditions/{condition_id}",
                    description=f"从组合中移除工况 {condition_id}")
        
        # 2.7 获取组合中的输出
        test_api("GET", f"/cond-out-groups/{group_id}/outputs",
                description="获取组合中的输出")
        
        # 2.8 添加输出到组合
        output_defs = test_api("GET", "/config/output-defs", description="获取输出定义列表")
        if output_defs and len(output_defs) > 0:
            output_id = output_defs[0]['id']
            test_api("POST", f"/cond-out-groups/{group_id}/outputs",
                    data={"outputDefId": output_id, "sort": 10},
                    description=f"添加输出 {output_id} 到组合")
            
            # 2.9 从组合中移除输出
            test_api("DELETE", f"/cond-out-groups/{group_id}/outputs/{output_id}",
                    description=f"从组合中移除输出 {output_id}")
        
        # 2.10 删除工况输出组合
        test_api("DELETE", f"/cond-out-groups/{group_id}",
                description="删除工况输出组合")
    
    print("\n\n" + "="*60)
    print("组合配置 API 测试完成")
    print("="*60)

if __name__ == "__main__":
    test_group_config_apis()

