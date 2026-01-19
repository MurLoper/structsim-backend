"""
后端 API 测试脚本
测试所有基础配置 API 的 CRUD 功能
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
                print(f"返回数据: {json.dumps(result['data'], ensure_ascii=False, indent=2)[:200]}...")
            return result.get('data')
        else:
            print(f"✗ 失败: {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ 异常: {e}")
        return None

def test_basic_config_apis():
    """测试基础配置 API"""
    
    print("\n" + "="*60)
    print("开始测试基础配置 API")
    print("="*60)
    
    # 1. 测试项目管理 API
    print("\n\n【1. 项目管理 API】")
    projects = test_api("GET", "/config/projects", description="获取项目列表")

    new_project = test_api("POST", "/config/projects",
                           data={"name": "测试项目", "code": random_code("PRJ"), "sort": 100},
                           description="创建项目")

    if new_project:
        project_id = new_project.get('id')
        test_api("PUT", f"/config/projects/{project_id}",
                data={"name": "测试项目（已更新）", "remark": "这是测试备注"},
                description="更新项目")

        test_api("DELETE", f"/config/projects/{project_id}",
                description="删除项目")

    # 2. 测试仿真类型 API
    print("\n\n【2. 仿真类型 API】")
    sim_types = test_api("GET", "/config/sim-types", description="获取仿真类型列表")

    new_sim_type = test_api("POST", "/config/sim-types",
                            data={"name": "测试仿真", "code": random_code("SIM"), "category": "STRUCTURE", "sort": 100},
                            description="创建仿真类型")
    
    if new_sim_type:
        sim_type_id = new_sim_type.get('id')
        test_api("PUT", f"/config/sim-types/{sim_type_id}",
                data={"name": "测试仿真（已更新）"},
                description="更新仿真类型")
        
        test_api("DELETE", f"/config/sim-types/{sim_type_id}",
                description="删除仿真类型")
    
    # 3. 测试参数定义 API
    print("\n\n【3. 参数定义 API】")
    param_defs = test_api("GET", "/config/param-defs", description="获取参数定义列表")

    new_param = test_api("POST", "/config/param-defs",
                         data={
                             "name": "测试参数",
                             "key": random_code("param").lower(),
                             "valType": 1,
                             "unit": "mm",
                             "minVal": 0,
                             "maxVal": 100,
                             "defaultVal": "50",
                             "precision": 2,
                             "sort": 100
                         },
                         description="创建参数定义")

    if new_param:
        param_id = new_param.get('id')
        test_api("PUT", f"/config/param-defs/{param_id}",
                data={"name": "测试参数（已更新）", "maxVal": 200},
                description="更新参数定义")

        test_api("DELETE", f"/config/param-defs/{param_id}",
                description="删除参数定义")

    # 4. 测试求解器 API
    print("\n\n【4. 求解器 API】")
    solvers = test_api("GET", "/config/solvers", description="获取求解器列表")

    new_solver = test_api("POST", "/config/solvers",
                          data={
                              "name": "测试求解器",
                              "code": random_code("SOLVER"),
                              "version": "1.0",
                              "cpuCoreMin": 1,
                              "cpuCoreMax": 64,
                              "cpuCoreDefault": 8,
                              "memoryMin": 1,
                              "memoryMax": 1024,
                              "memoryDefault": 64,
                              "sort": 100
                          },
                          description="创建求解器")
    
    if new_solver:
        solver_id = new_solver.get('id')
        test_api("PUT", f"/config/solvers/{solver_id}",
                data={"name": "测试求解器（已更新）", "version": "2.0"},
                description="更新求解器")
        
        test_api("DELETE", f"/config/solvers/{solver_id}",
                description="删除求解器")
    
    # 5. 测试工况定义 API
    print("\n\n【5. 工况定义 API】")
    condition_defs = test_api("GET", "/config/condition-defs", description="获取工况定义列表")

    new_condition = test_api("POST", "/config/condition-defs",
                             data={
                                 "name": "测试工况",
                                 "code": random_code("COND"),
                                 "category": "载荷",
                                 "unit": "N",
                                 "sort": 100
                             },
                             description="创建工况定义")

    if new_condition:
        condition_id = new_condition.get('id')
        test_api("PUT", f"/config/condition-defs/{condition_id}",
                data={"name": "测试工况（已更新）", "unit": "kN"},
                description="更新工况定义")

        test_api("DELETE", f"/config/condition-defs/{condition_id}",
                description="删除工况定义")

    # 6. 测试输出定义 API
    print("\n\n【6. 输出定义 API】")
    output_defs = test_api("GET", "/config/output-defs", description="获取输出定义列表")

    new_output = test_api("POST", "/config/output-defs",
                          data={
                              "name": "测试输出",
                              "code": random_code("OUT"),
                              "unit": "mm",
                              "valType": 1,
                              "sort": 100
                          },
                          description="创建输出定义")

    if new_output:
        output_id = new_output.get('id')
        test_api("PUT", f"/config/output-defs/{output_id}",
                data={"name": "测试输出（已更新）", "unit": "m"},
                description="更新输出定义")

        test_api("DELETE", f"/config/output-defs/{output_id}",
                description="删除输出定义")

    # 7. 测试姿态类型 API
    print("\n\n【7. 姿态类型 API】")
    fold_types = test_api("GET", "/config/fold-types", description="获取姿态类型列表")

    new_fold_type = test_api("POST", "/config/fold-types",
                             data={
                                 "name": "测试姿态",
                                 "code": random_code("FOLD"),
                                 "angle": 45,
                                 "sort": 100
                             },
                             description="创建姿态类型")
    
    if new_fold_type:
        fold_type_id = new_fold_type.get('id')
        test_api("PUT", f"/config/fold-types/{fold_type_id}",
                data={"name": "测试姿态（已更新）", "angle": 90},
                description="更新姿态类型")
        
        test_api("DELETE", f"/config/fold-types/{fold_type_id}",
                description="删除姿态类型")
    
    print("\n\n" + "="*60)
    print("基础配置 API 测试完成")
    print("="*60)

if __name__ == "__main__":
    test_basic_config_apis()

