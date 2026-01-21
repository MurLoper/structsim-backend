OPENAPI_SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "StructSim AI Platform API",
        "version": "1.0.0",
        "description": "StructSim AI Platform REST API",
    },
    "servers": [
        {"url": "/"}
    ],
    "tags": [
        {"name": "health", "description": "Health check"},
        {"name": "auth", "description": "Authentication"},
        {"name": "config", "description": "Configuration"},
        {"name": "orders", "description": "Orders"},
        {"name": "rbac", "description": "RBAC"},
        {"name": "param-groups", "description": "Param group management"},
        {"name": "cond-out-groups", "description": "Condition/output group management"},
        {"name": "relations", "description": "Config relations"},
        {"name": "projects", "description": "Legacy projects"},
        {"name": "results", "description": "Legacy results"}
    ],
    "components": {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        },
        "schemas": {
            "StandardResponse": {
                "type": "object",
                "properties": {
                    "code": {"type": "integer"},
                    "msg": {"type": "string"},
                    "data": {},
                    "trace_id": {"type": "string"},
                },
            },
            "ErrorResponse": {
                "type": "object",
                "properties": {
                    "code": {"type": "integer"},
                    "msg": {"type": "string"},
                    "data": {"nullable": True},
                    "trace_id": {"type": "string"},
                },
            },
            "LoginRequest": {
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                    "password": {"type": "string"}
                },
                "required": ["email", "password"]
            },
            "UserPublicInfo": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "username": {"type": "string"},
                    "email": {"type": "string"},
                    "role": {"type": "string"}
                }
            },
            "LoginResponse": {
                "type": "object",
                "properties": {
                    "token": {"type": "string"},
                    "user": {"$ref": "#/components/schemas/UserPublicInfo"}
                }
            },
            "OriginFile": {
                "type": "object",
                "properties": {
                    "type": {"type": "integer"},
                    "path": {"type": "string", "nullable": True},
                    "name": {"type": "string", "nullable": True},
                    "fileId": {"type": "integer", "nullable": True}
                }
            },
            "OrderCreate": {
                "type": "object",
                "properties": {
                    "projectId": {"type": "integer"},
                    "originFile": {"$ref": "#/components/schemas/OriginFile"},
                    "foldTypeId": {"type": "integer", "nullable": True},
                    "participantUids": {"type": "array", "items": {"type": "integer"}},
                    "remark": {"type": "string", "nullable": True},
                    "simTypeIds": {"type": "array", "items": {"type": "integer"}},
                    "optParam": {"type": "object", "nullable": True},
                    "workflowId": {"type": "integer", "nullable": True},
                    "submitCheck": {"type": "object", "nullable": True},
                    "clientMeta": {"type": "object", "nullable": True}
                },
                "required": ["projectId", "originFile"]
            },

            "OrderUpdate": {
                "type": "object",
                "properties": {
                    "remark": {"type": "string", "nullable": True},
                    "participantUids": {"type": "array", "items": {"type": "integer"}},
                    "optParam": {"type": "object", "nullable": True}
                }
            },
            "OrderQuery": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer"},
                    "pageSize": {"type": "integer"},
                    "status": {"type": "integer", "nullable": True},
                    "projectId": {"type": "integer", "nullable": True}
                }
            },
            "OrderInitConfigResponse": {
                "type": "object",
                "properties": {
                    "projectId": {"type": "integer"},
                    "projectName": {"type": "string"},
                    "simTypeId": {"type": "integer"},
                    "simTypeName": {"type": "string"},
                    "simTypeCode": {"type": "string"},
                    "defaultParamGroup": {"$ref": "#/components/schemas/ParamGroupOption"},
                    "paramGroupOptions": {"type": "array", "items": {"$ref": "#/components/schemas/ParamGroupOption"}},
                    "defaultCondOutGroup": {"$ref": "#/components/schemas/CondOutGroupOption"},
                    "condOutGroupOptions": {"type": "array", "items": {"$ref": "#/components/schemas/CondOutGroupOption"}},
                    "defaultSolver": {"$ref": "#/components/schemas/SolverOption"},
                    "solverOptions": {"type": "array", "items": {"$ref": "#/components/schemas/SolverOption"}}
                }
            },
            "ParamGroupOption": {
                "type": "object",
                "properties": {
                    "paramGroupId": {"type": "integer"},
                    "paramGroupName": {"type": "string"},
                    "isDefault": {"type": "boolean"},
                    "params": {"type": "array", "items": {"$ref": "#/components/schemas/ParamGroupParamItem"}}
                }
            },
            "ParamGroupParamItem": {
                "type": "object",
                "properties": {
                    "paramDefId": {"type": "integer"},
                    "paramName": {"type": "string"},
                    "paramKey": {"type": "string"},
                    "defaultValue": {"nullable": True},
                    "unit": {"type": "string", "nullable": True},
                    "valType": {"type": "string"},
                    "required": {"type": "boolean"}
                }
            },
            "CondOutGroupOption": {
                "type": "object",
                "properties": {
                    "condOutGroupId": {"type": "integer"},
                    "condOutGroupName": {"type": "string"},
                    "isDefault": {"type": "boolean"},
                    "conditions": {"type": "array", "items": {"$ref": "#/components/schemas/CondOutGroupConditionItem"}},
                    "outputs": {"type": "array", "items": {"$ref": "#/components/schemas/CondOutGroupOutputItem"}}
                }
            },
            "CondOutGroupConditionItem": {
                "type": "object",
                "properties": {
                    "conditionDefId": {"type": "integer"},
                    "conditionName": {"type": "string"},
                    "conditionCode": {"type": "string"},
                    "configData": {"nullable": True},
                    "conditionSchema": {"nullable": True}
                }
            },
            "CondOutGroupOutputItem": {
                "type": "object",
                "properties": {
                    "outputDefId": {"type": "integer"},
                    "outputName": {"type": "string"},
                    "outputCode": {"type": "string"},
                    "unit": {"type": "string", "nullable": True},
                    "valType": {"type": "string"}
                }
            },
            "SolverOption": {
                "type": "object",
                "properties": {
                    "solverId": {"type": "integer"},
                    "solverName": {"type": "string"},
                    "solverCode": {"type": "string"},
                    "solverVersion": {"type": "string", "nullable": True},
                    "isDefault": {"type": "boolean"}
                }
            },
            "UserCreate": {
                "type": "object",
                "properties": {
                    "username": {"type": "string"},
                    "email": {"type": "string"},
                    "name": {"type": "string", "nullable": True},
                    "password": {"type": "string", "nullable": True},
                    "avatar": {"type": "string", "nullable": True},
                    "phone": {"type": "string", "nullable": True},
                    "department": {"type": "string", "nullable": True},
                    "roleIds": {"type": "array", "items": {"type": "integer"}},
                    "valid": {"type": "integer", "nullable": True}
                },
                "required": ["username", "email"]
            },
            "UserUpdate": {
                "type": "object",
                "properties": {
                    "username": {"type": "string", "nullable": True},
                    "email": {"type": "string", "nullable": True},
                    "name": {"type": "string", "nullable": True},
                    "password": {"type": "string", "nullable": True},
                    "avatar": {"type": "string", "nullable": True},
                    "phone": {"type": "string", "nullable": True},
                    "department": {"type": "string", "nullable": True},
                    "roleIds": {"type": "array", "items": {"type": "integer"}},
                    "valid": {"type": "integer", "nullable": True}
                }
            },
            "RoleCreate": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "code": {"type": "string", "nullable": True},
                    "description": {"type": "string", "nullable": True},
                    "permissionIds": {"type": "array", "items": {"type": "integer"}},
                    "valid": {"type": "integer", "nullable": True},
                    "sort": {"type": "integer", "nullable": True}
                },
                "required": ["name"]
            },
            "RoleUpdate": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "nullable": True},
                    "code": {"type": "string", "nullable": True},
                    "description": {"type": "string", "nullable": True},
                    "permissionIds": {"type": "array", "items": {"type": "integer"}},
                    "valid": {"type": "integer", "nullable": True},
                    "sort": {"type": "integer", "nullable": True}
                }
            },
            "PermissionCreate": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "code": {"type": "string"},
                    "type": {"type": "string", "nullable": True},
                    "resource": {"type": "string", "nullable": True},
                    "description": {"type": "string", "nullable": True},
                    "valid": {"type": "integer", "nullable": True},
                    "sort": {"type": "integer", "nullable": True}
                },
                "required": ["name", "code"]
            },
            "PermissionUpdate": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "nullable": True},
                    "code": {"type": "string", "nullable": True},
                    "type": {"type": "string", "nullable": True},
                    "resource": {"type": "string", "nullable": True},
                    "description": {"type": "string", "nullable": True},
                    "valid": {"type": "integer", "nullable": True},
                    "sort": {"type": "integer", "nullable": True}
                }
            },
            "ProjectCreate": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "code": {"type": "string", "nullable": True},
                    "default_sim_type_id": {"type": "integer", "nullable": True},
                    "default_solver_id": {"type": "integer", "nullable": True},
                    "sort": {"type": "integer", "nullable": True},
                    "remark": {"type": "string", "nullable": True}
                },
                "required": ["name"]
            },
            "ProjectUpdate": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "nullable": True},
                    "code": {"type": "string", "nullable": True},
                    "default_sim_type_id": {"type": "integer", "nullable": True},
                    "default_solver_id": {"type": "integer", "nullable": True},
                    "sort": {"type": "integer", "nullable": True},
                    "remark": {"type": "string", "nullable": True}
                }
            },
            "SimTypeCreate": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "code": {"type": "string", "nullable": True},
                    "category": {"type": "string", "nullable": True},
                    "support_alg_mask": {"type": "integer"},
                    "node_icon": {"type": "string", "nullable": True},
                    "color_tag": {"type": "string", "nullable": True},
                    "sort": {"type": "integer"},
                    "remark": {"type": "string", "nullable": True}
                },
                "required": ["name", "support_alg_mask", "sort"]
            },
            "SimTypeUpdate": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "nullable": True},
                    "code": {"type": "string", "nullable": True},
                    "category": {"type": "string", "nullable": True},
                    "support_alg_mask": {"type": "integer", "nullable": True},
                    "node_icon": {"type": "string", "nullable": True},
                    "color_tag": {"type": "string", "nullable": True},
                    "sort": {"type": "integer", "nullable": True},
                    "remark": {"type": "string", "nullable": True}
                }
            },
            "ParamDefCreate": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "key": {"type": "string"},
                    "val_type": {"type": "string"},
                    "unit": {"type": "string", "nullable": True},
                    "min_val": {"type": "number", "nullable": True},
                    "max_val": {"type": "number", "nullable": True},
                    "default_val": {"nullable": True},
                    "precision": {"type": "integer"},
                    "enum_options": {"nullable": True},
                    "required": {"type": "boolean"},
                    "sort": {"type": "integer"},
                    "remark": {"type": "string", "nullable": True}
                },
                "required": ["name", "key", "val_type", "precision", "required", "sort"]
            },
            "ParamDefUpdate": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "nullable": True},
                    "key": {"type": "string", "nullable": True},
                    "valType": {"type": "string", "nullable": True},
                    "unit": {"type": "string", "nullable": True},
                    "minVal": {"type": "number", "nullable": True},
                    "maxVal": {"type": "number", "nullable": True},
                    "defaultVal": {"nullable": True},
                    "precision": {"type": "integer", "nullable": True},
                    "enumOptions": {"nullable": True},
                    "required": {"type": "boolean", "nullable": True},
                    "sort": {"type": "integer", "nullable": True},
                    "remark": {"type": "string", "nullable": True}
                }
            },
            "SolverCreate": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "code": {"type": "string", "nullable": True},
                    "version": {"type": "string", "nullable": True},
                    "cpu_core_min": {"type": "integer"},
                    "cpu_core_max": {"type": "integer"},
                    "cpu_core_default": {"type": "integer"},
                    "memory_min": {"type": "integer"},
                    "memory_max": {"type": "integer"},
                    "memory_default": {"type": "integer"},
                    "sort": {"type": "integer"},
                    "remark": {"type": "string", "nullable": True}
                },
                "required": ["name", "cpu_core_min", "cpu_core_max", "cpu_core_default", "memory_min", "memory_max", "memory_default", "sort"]
            },
            "SolverUpdate": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "nullable": True},
                    "code": {"type": "string", "nullable": True},
                    "version": {"type": "string", "nullable": True},
                    "cpu_core_min": {"type": "integer", "nullable": True},
                    "cpu_core_max": {"type": "integer", "nullable": True},
                    "cpu_core_default": {"type": "integer", "nullable": True},
                    "memory_min": {"type": "integer", "nullable": True},
                    "memory_max": {"type": "integer", "nullable": True},
                    "memory_default": {"type": "integer", "nullable": True},
                    "sort": {"type": "integer", "nullable": True},
                    "remark": {"type": "string", "nullable": True}
                }
            },
            "ConditionDefCreate": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "code": {"type": "string", "nullable": True},
                    "category": {"type": "string", "nullable": True},
                    "unit": {"type": "string", "nullable": True},
                    "sort": {"type": "integer"},
                    "remark": {"type": "string", "nullable": True}
                },
                "required": ["name", "sort"]
            },
            "ConditionDefUpdate": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "nullable": True},
                    "code": {"type": "string", "nullable": True},
                    "category": {"type": "string", "nullable": True},
                    "unit": {"type": "string", "nullable": True},
                    "sort": {"type": "integer", "nullable": True},
                    "remark": {"type": "string", "nullable": True}
                }
            },
            "OutputDefCreate": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "code": {"type": "string", "nullable": True},
                    "unit": {"type": "string", "nullable": True},
                    "val_type": {"type": "string"},
                    "sort": {"type": "integer"},
                    "remark": {"type": "string", "nullable": True}
                },
                "required": ["name", "val_type", "sort"]
            },
            "OutputDefUpdate": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "nullable": True},
                    "code": {"type": "string", "nullable": True},
                    "unit": {"type": "string", "nullable": True},
                    "valType": {"type": "string", "nullable": True},
                    "sort": {"type": "integer", "nullable": True},
                    "remark": {"type": "string", "nullable": True}
                }
            },
            "FoldTypeCreate": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "code": {"type": "string", "nullable": True},
                    "angle": {"type": "number"},
                    "sort": {"type": "integer"},
                    "remark": {"type": "string", "nullable": True}
                },
                "required": ["name", "angle", "sort"]
            },
            "FoldTypeUpdate": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "nullable": True},
                    "code": {"type": "string", "nullable": True},
                    "angle": {"type": "number", "nullable": True},
                    "sort": {"type": "integer", "nullable": True},
                    "remark": {"type": "string", "nullable": True}
                }
            },
            "ParamGroupCreateRequest": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string", "nullable": True},
                    "sort": {"type": "integer", "nullable": True}
                },
                "required": ["name"]
            },
            "ParamGroupUpdateRequest": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "nullable": True},
                    "description": {"type": "string", "nullable": True},
                    "valid": {"type": "integer", "nullable": True},
                    "sort": {"type": "integer", "nullable": True}
                }
            },
            "AddParamToGroupRequest": {
                "type": "object",
                "properties": {
                    "paramDefId": {"type": "integer"},
                    "defaultValue": {"nullable": True},
                    "sort": {"type": "integer", "nullable": True}
                },
                "required": ["paramDefId"]
            },
            "ParamGroupResponse": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "description": {"type": "string", "nullable": True},
                    "valid": {"type": "integer"},
                    "sort": {"type": "integer"}
                }
            },
            "ParamGroupDetailResponse": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "description": {"type": "string", "nullable": True},
                    "valid": {"type": "integer"},
                    "sort": {"type": "integer"},
                    "params": {"type": "array", "items": {"$ref": "#/components/schemas/ParamGroupParamItem"}}
                }
            },
            "CondOutGroupCreateRequest": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string", "nullable": True},
                    "sort": {"type": "integer", "nullable": True}
                },
                "required": ["name"]
            },
            "CondOutGroupUpdateRequest": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "nullable": True},
                    "description": {"type": "string", "nullable": True},
                    "valid": {"type": "integer", "nullable": True},
                    "sort": {"type": "integer", "nullable": True}
                }
            },
            "AddConditionToGroupRequest": {
                "type": "object",
                "properties": {
                    "conditionDefId": {"type": "integer"},
                    "configData": {"nullable": True},
                    "sort": {"type": "integer", "nullable": True}
                },
                "required": ["conditionDefId"]
            },
            "AddOutputToGroupRequest": {
                "type": "object",
                "properties": {
                    "outputDefId": {"type": "integer"},
                    "sort": {"type": "integer", "nullable": True}
                },
                "required": ["outputDefId"]
            },
            "CondOutGroupDetailResponse": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "description": {"type": "string", "nullable": True},
                    "valid": {"type": "integer"},
                    "sort": {"type": "integer"},
                    "conditions": {"type": "array", "items": {"$ref": "#/components/schemas/CondOutGroupConditionItem"}},
                    "outputs": {"type": "array", "items": {"$ref": "#/components/schemas/CondOutGroupOutputItem"}}
                }
            },
            "ProjectSimTypeRelCreateRequest": {
                "type": "object",
                "properties": {
                    "simTypeId": {"type": "integer"},
                    "isDefault": {"type": "boolean", "nullable": True},
                    "sort": {"type": "integer", "nullable": True}
                },
                "required": ["simTypeId"]
            },
            "SimTypeParamGroupRelCreateRequest": {
                "type": "object",
                "properties": {
                    "paramGroupId": {"type": "integer"},
                    "isDefault": {"type": "boolean", "nullable": True},
                    "sort": {"type": "integer", "nullable": True}
                },
                "required": ["paramGroupId"]
            },
            "SimTypeCondOutGroupRelCreateRequest": {
                "type": "object",
                "properties": {
                    "condOutGroupId": {"type": "integer"},
                    "isDefault": {"type": "boolean", "nullable": True},
                    "sort": {"type": "integer", "nullable": True}
                },
                "required": ["condOutGroupId"]
            },
            "SimTypeSolverRelCreateRequest": {
                "type": "object",
                "properties": {
                    "solverId": {"type": "integer"},
                    "isDefault": {"type": "boolean", "nullable": True},
                    "sort": {"type": "integer", "nullable": True}
                },
                "required": ["solverId"]
            },
            "AnalysisRequest": {
                "type": "object",
                "properties": {
                    "orderId": {"type": "integer"},
                    "simTypeId": {"type": "integer"},
                    "chartType": {"type": "string", "nullable": True},
                    "xField": {"type": "string", "nullable": True},
                    "yField": {"type": "string", "nullable": True},
                    "zField": {"type": "string", "nullable": True},
                    "filters": {"nullable": True},
                    "sampling": {"nullable": True}
                },
                "required": ["orderId", "simTypeId"]
            },
            "AnalysisResponse": {
                "type": "object",
                "properties": {
                    "chartType": {"type": "string"},
                    "data": {"type": "array", "items": {"type": "object"}},
                    "totalPoints": {"type": "integer"},
                    "sampled": {"type": "boolean"}
                }
            }
        },
    },
    "paths": {
        "/health": {
            "get": {
                "tags": ["health"],
                "summary": "Health check",
                "responses": {
                    "200": {"description": "OK"}
                },
            }
        },
        "/api/v1/auth/login": {
            "post": {
                "tags": ["auth"],
                "summary": "Login",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/LoginRequest"}
                        }
                    }
                },
                "responses": {
                    "200": {"$ref": "#/components/schemas/StandardResponse"},
                    "400": {"$ref": "#/components/schemas/ErrorResponse"}
                }
            }
        },
        "/api/v1/auth/me": {
            "get": {
                "tags": ["auth"],
                "summary": "Get current user",
                "security": [{"BearerAuth": []}],
                "responses": {
                    "200": {"$ref": "#/components/schemas/StandardResponse"},
                    "404": {"$ref": "#/components/schemas/ErrorResponse"}
                }
            }
        },
        "/api/v1/auth/users": {
            "get": {
                "tags": ["auth"],
                "summary": "List users (login selector)",
                "responses": {
                    "200": {"$ref": "#/components/schemas/StandardResponse"}
                }
            }
        },
        "/api/v1/auth/logout": {
            "post": {
                "tags": ["auth"],
                "summary": "Logout",
                "security": [{"BearerAuth": []}],
                "responses": {
                    "200": {"$ref": "#/components/schemas/StandardResponse"}
                }
            }
        },
        "/api/v1/config/projects": {
            "get": {
                "tags": ["config"],
                "summary": "List projects",
                "responses": {
                    "200": {"$ref": "#/components/schemas/StandardResponse"}
                }
            },
            "post": {
                "tags": ["config"],
                "summary": "Create project",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ProjectCreate"}}}
                },
                "responses": {
                    "200": {"$ref": "#/components/schemas/StandardResponse"},
                    "400": {"$ref": "#/components/schemas/ErrorResponse"}
                }
            }
        },
        "/api/v1/config/projects/{id}": {
            "get": {
                "tags": ["config"],
                "summary": "Get project",
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {
                    "200": {"$ref": "#/components/schemas/StandardResponse"},
                    "404": {"$ref": "#/components/schemas/ErrorResponse"}
                }
            },
            "put": {
                "tags": ["config"],
                "summary": "Update project",
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ProjectUpdate"}}}
                },
                "responses": {
                    "200": {"$ref": "#/components/schemas/StandardResponse"},
                    "400": {"$ref": "#/components/schemas/ErrorResponse"}
                }
            },
            "delete": {
                "tags": ["config"],
                "summary": "Delete project",
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {
                    "200": {"$ref": "#/components/schemas/StandardResponse"},
                    "404": {"$ref": "#/components/schemas/ErrorResponse"}
                }
            }
        },
        "/api/v1/config/sim-types": {
            "get": {
                "tags": ["config"],
                "summary": "List sim types",
                "responses": {
                    "200": {"$ref": "#/components/schemas/StandardResponse"}
                }
            },
            "post": {
                "tags": ["config"],
                "summary": "Create sim type",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/SimTypeCreate"}}}
                },
                "responses": {
                    "200": {"$ref": "#/components/schemas/StandardResponse"}
                }
            }
        },
        "/api/v1/config/sim-types/{id}": {
            "get": {
                "tags": ["config"],
                "summary": "Get sim type",
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "put": {
                "tags": ["config"],
                "summary": "Update sim type",
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/SimTypeUpdate"}}}
                },
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "delete": {
                "tags": ["config"],
                "summary": "Delete sim type",
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/config/param-defs": {
            "get": {
                "tags": ["config"],
                "summary": "List param defs",
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "post": {
                "tags": ["config"],
                "summary": "Create param def",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ParamDefCreate"}}}
                },
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/config/param-defs/{id}": {
            "put": {
                "tags": ["config"],
                "summary": "Update param def",
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ParamDefUpdate"}}}
                },
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "delete": {
                "tags": ["config"],
                "summary": "Delete param def",
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/config/solvers": {
            "get": {
                "tags": ["config"],
                "summary": "List solvers",
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "post": {
                "tags": ["config"],
                "summary": "Create solver",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/SolverCreate"}}}
                },
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/config/solvers/{id}": {
            "put": {
                "tags": ["config"],
                "summary": "Update solver",
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/SolverUpdate"}}}
                },
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "delete": {
                "tags": ["config"],
                "summary": "Delete solver",
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/config/condition-defs": {
            "get": {
                "tags": ["config"],
                "summary": "List condition defs",
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "post": {
                "tags": ["config"],
                "summary": "Create condition def",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ConditionDefCreate"}}}
                },
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/config/condition-defs/{id}": {
            "put": {
                "tags": ["config"],
                "summary": "Update condition def",
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ConditionDefUpdate"}}}
                },
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "delete": {
                "tags": ["config"],
                "summary": "Delete condition def",
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/config/output-defs": {
            "get": {
                "tags": ["config"],
                "summary": "List output defs",
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "post": {
                "tags": ["config"],
                "summary": "Create output def",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/OutputDefCreate"}}}
                },
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/config/output-defs/{id}": {
            "put": {
                "tags": ["config"],
                "summary": "Update output def",
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/OutputDefUpdate"}}}
                },
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "delete": {
                "tags": ["config"],
                "summary": "Delete output def",
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/config/fold-types": {
            "get": {
                "tags": ["config"],
                "summary": "List fold types",
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "post": {
                "tags": ["config"],
                "summary": "Create fold type",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/FoldTypeCreate"}}}
                },
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/config/fold-types/{id}": {
            "put": {
                "tags": ["config"],
                "summary": "Update fold type",
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/FoldTypeUpdate"}}}
                },
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "delete": {
                "tags": ["config"],
                "summary": "Delete fold type",
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/config/param-tpl-sets": {
            "get": {
                "tags": ["config"],
                "summary": "List param template sets",
                "parameters": [
                    {"name": "simTypeId", "in": "query", "required": False, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/config/cond-out-sets": {
            "get": {
                "tags": ["config"],
                "summary": "List condition/output sets",
                "parameters": [
                    {"name": "simTypeId", "in": "query", "required": False, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/config/workflows": {
            "get": {
                "tags": ["config"],
                "summary": "List workflows",
                "parameters": [
                    {"name": "type", "in": "query", "required": False, "schema": {"type": "string"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/config/status-defs": {
            "get": {
                "tags": ["config"],
                "summary": "List status defs",
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/config/automation-modules": {
            "get": {
                "tags": ["config"],
                "summary": "List automation modules",
                "parameters": [
                    {"name": "category", "in": "query", "required": False, "schema": {"type": "string"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/config/base-data": {
            "get": {
                "tags": ["config"],
                "summary": "Get base data",
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/orders": {
            "get": {
                "tags": ["orders"],
                "summary": "List orders",
                "security": [{"BearerAuth": []}],
                "parameters": [
                    {"name": "page", "in": "query", "required": False, "schema": {"type": "integer"}},
                    {"name": "pageSize", "in": "query", "required": False, "schema": {"type": "integer"}},
                    {"name": "status", "in": "query", "required": False, "schema": {"type": "integer"}},
                    {"name": "projectId", "in": "query", "required": False, "schema": {"type": "integer"}}
                ],
                "responses": {
                    "200": {"$ref": "#/components/schemas/StandardResponse"}
                }
            },
            "post": {
                "tags": ["orders"],
                "summary": "Create order",
                "security": [{"BearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/OrderCreate"}}}
                },
                "responses": {
                    "200": {"$ref": "#/components/schemas/StandardResponse"}
                }
            }
        },
        "/api/v1/orders/{order_id}": {
            "get": {
                "tags": ["orders"],
                "summary": "Get order",
                "security": [{"BearerAuth": []}],
                "parameters": [
                    {"name": "order_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "put": {
                "tags": ["orders"],
                "summary": "Update order",
                "security": [{"BearerAuth": []}],
                "parameters": [
                    {"name": "order_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/OrderUpdate"}}}
                },
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "delete": {
                "tags": ["orders"],
                "summary": "Delete order",
                "security": [{"BearerAuth": []}],
                "parameters": [
                    {"name": "order_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/orders/{order_id}/result": {
            "get": {
                "tags": ["orders"],
                "summary": "Get order result",
                "security": [{"BearerAuth": []}],
                "parameters": [
                    {"name": "order_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/orders/init-config": {
            "get": {
                "tags": ["orders"],
                "summary": "Get init config",
                "parameters": [
                    {"name": "projectId", "in": "query", "required": True, "schema": {"type": "integer"}},
                    {"name": "simTypeId", "in": "query", "required": False, "schema": {"type": "integer"}}
                ],
                "responses": {
                    "200": {"$ref": "#/components/schemas/StandardResponse"},
                    "400": {"$ref": "#/components/schemas/ErrorResponse"}
                }
            }
        },
        "/api/v1/rbac/users": {
            "get": {
                "tags": ["rbac"],
                "summary": "List users",
                "security": [{"BearerAuth": []}],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "post": {
                "tags": ["rbac"],
                "summary": "Create user",
                "security": [{"BearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserCreate"}}}
                },
                "responses": {
                    "200": {"$ref": "#/components/schemas/StandardResponse"},
                    "400": {"$ref": "#/components/schemas/ErrorResponse"}
                }
            }
        },
        "/api/v1/rbac/users/{id}": {
            "put": {
                "tags": ["rbac"],
                "summary": "Update user",
                "security": [{"BearerAuth": []}],
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/UserUpdate"}}}
                },
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "delete": {
                "tags": ["rbac"],
                "summary": "Delete user",
                "security": [{"BearerAuth": []}],
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/rbac/roles": {
            "get": {
                "tags": ["rbac"],
                "summary": "List roles",
                "security": [{"BearerAuth": []}],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "post": {
                "tags": ["rbac"],
                "summary": "Create role",
                "security": [{"BearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/RoleCreate"}}}
                },
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/rbac/roles/{id}": {
            "put": {
                "tags": ["rbac"],
                "summary": "Update role",
                "security": [{"BearerAuth": []}],
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/RoleUpdate"}}}
                },
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "delete": {
                "tags": ["rbac"],
                "summary": "Delete role",
                "security": [{"BearerAuth": []}],
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/rbac/permissions": {
            "get": {
                "tags": ["rbac"],
                "summary": "List permissions",
                "security": [{"BearerAuth": []}],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "post": {
                "tags": ["rbac"],
                "summary": "Create permission",
                "security": [{"BearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/PermissionCreate"}}}
                },
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/rbac/permissions/{id}": {
            "put": {
                "tags": ["rbac"],
                "summary": "Update permission",
                "security": [{"BearerAuth": []}],
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/PermissionUpdate"}}}
                },
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "delete": {
                "tags": ["rbac"],
                "summary": "Delete permission",
                "security": [{"BearerAuth": []}],
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/param-groups": {
            "get": {
                "tags": ["param-groups"],
                "summary": "List param groups",
                "parameters": [
                    {"name": "valid", "in": "query", "required": False, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "post": {
                "tags": ["param-groups"],
                "summary": "Create param group",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ParamGroupCreateRequest"}}}
                },
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/param-groups/{group_id}": {
            "get": {
                "tags": ["param-groups"],
                "summary": "Get param group detail",
                "parameters": [
                    {"name": "group_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "put": {
                "tags": ["param-groups"],
                "summary": "Update param group",
                "parameters": [
                    {"name": "group_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ParamGroupUpdateRequest"}}}
                },
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "delete": {
                "tags": ["param-groups"],
                "summary": "Delete param group",
                "parameters": [
                    {"name": "group_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/param-groups/{group_id}/params": {
            "get": {
                "tags": ["param-groups"],
                "summary": "List params in group",
                "parameters": [
                    {"name": "group_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "post": {
                "tags": ["param-groups"],
                "summary": "Add param to group",
                "parameters": [
                    {"name": "group_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/AddParamToGroupRequest"}}}
                },
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/param-groups/{group_id}/params/{param_def_id}": {
            "delete": {
                "tags": ["param-groups"],
                "summary": "Remove param from group",
                "parameters": [
                    {"name": "group_id", "in": "path", "required": True, "schema": {"type": "integer"}},
                    {"name": "param_def_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/cond-out-groups": {
            "get": {
                "tags": ["cond-out-groups"],
                "summary": "List condition/output groups",
                "parameters": [
                    {"name": "valid", "in": "query", "required": False, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "post": {
                "tags": ["cond-out-groups"],
                "summary": "Create condition/output group",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/CondOutGroupCreateRequest"}}}
                },
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/cond-out-groups/{group_id}": {
            "get": {
                "tags": ["cond-out-groups"],
                "summary": "Get condition/output group detail",
                "parameters": [
                    {"name": "group_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "put": {
                "tags": ["cond-out-groups"],
                "summary": "Update condition/output group",
                "parameters": [
                    {"name": "group_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/CondOutGroupUpdateRequest"}}}
                },
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "delete": {
                "tags": ["cond-out-groups"],
                "summary": "Delete condition/output group",
                "parameters": [
                    {"name": "group_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/cond-out-groups/{group_id}/conditions": {
            "get": {
                "tags": ["cond-out-groups"],
                "summary": "List conditions in group",
                "parameters": [
                    {"name": "group_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "post": {
                "tags": ["cond-out-groups"],
                "summary": "Add condition to group",
                "parameters": [
                    {"name": "group_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/AddConditionToGroupRequest"}}}
                },
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/cond-out-groups/{group_id}/conditions/{condition_def_id}": {
            "delete": {
                "tags": ["cond-out-groups"],
                "summary": "Remove condition from group",
                "parameters": [
                    {"name": "group_id", "in": "path", "required": True, "schema": {"type": "integer"}},
                    {"name": "condition_def_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/cond-out-groups/{group_id}/outputs": {
            "get": {
                "tags": ["cond-out-groups"],
                "summary": "List outputs in group",
                "parameters": [
                    {"name": "group_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "post": {
                "tags": ["cond-out-groups"],
                "summary": "Add output to group",
                "parameters": [
                    {"name": "group_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/AddOutputToGroupRequest"}}}
                },
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/cond-out-groups/{group_id}/outputs/{output_def_id}": {
            "delete": {
                "tags": ["cond-out-groups"],
                "summary": "Remove output from group",
                "parameters": [
                    {"name": "group_id", "in": "path", "required": True, "schema": {"type": "integer"}},
                    {"name": "output_def_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/projects/{project_id}/sim-types": {
            "get": {
                "tags": ["relations"],
                "summary": "List project sim types",
                "parameters": [
                    {"name": "project_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "post": {
                "tags": ["relations"],
                "summary": "Add sim type to project",
                "parameters": [
                    {"name": "project_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ProjectSimTypeRelCreateRequest"}}}
                },
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/projects/{project_id}/sim-types/{sim_type_id}/default": {
            "put": {
                "tags": ["relations"],
                "summary": "Set default sim type for project",
                "parameters": [
                    {"name": "project_id", "in": "path", "required": True, "schema": {"type": "integer"}},
                    {"name": "sim_type_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/projects/{project_id}/sim-types/{sim_type_id}": {
            "delete": {
                "tags": ["relations"],
                "summary": "Remove sim type from project",
                "parameters": [
                    {"name": "project_id", "in": "path", "required": True, "schema": {"type": "integer"}},
                    {"name": "sim_type_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/sim-types/{sim_type_id}/param-groups": {
            "get": {
                "tags": ["relations"],
                "summary": "List sim type param groups",
                "parameters": [
                    {"name": "sim_type_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "post": {
                "tags": ["relations"],
                "summary": "Add param group to sim type",
                "parameters": [
                    {"name": "sim_type_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/SimTypeParamGroupRelCreateRequest"}}}
                },
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/sim-types/{sim_type_id}/param-groups/{param_group_id}/default": {
            "put": {
                "tags": ["relations"],
                "summary": "Set default param group for sim type",
                "parameters": [
                    {"name": "sim_type_id", "in": "path", "required": True, "schema": {"type": "integer"}},
                    {"name": "param_group_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/sim-types/{sim_type_id}/param-groups/{param_group_id}": {
            "delete": {
                "tags": ["relations"],
                "summary": "Remove param group from sim type",
                "parameters": [
                    {"name": "sim_type_id", "in": "path", "required": True, "schema": {"type": "integer"}},
                    {"name": "param_group_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/sim-types/{sim_type_id}/cond-out-groups": {
            "get": {
                "tags": ["relations"],
                "summary": "List sim type cond/out groups",
                "parameters": [
                    {"name": "sim_type_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "post": {
                "tags": ["relations"],
                "summary": "Add cond/out group to sim type",
                "parameters": [
                    {"name": "sim_type_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/SimTypeCondOutGroupRelCreateRequest"}}}
                },
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/sim-types/{sim_type_id}/cond-out-groups/{cond_out_group_id}/default": {
            "put": {
                "tags": ["relations"],
                "summary": "Set default cond/out group for sim type",
                "parameters": [
                    {"name": "sim_type_id", "in": "path", "required": True, "schema": {"type": "integer"}},
                    {"name": "cond_out_group_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/sim-types/{sim_type_id}/cond-out-groups/{cond_out_group_id}": {
            "delete": {
                "tags": ["relations"],
                "summary": "Remove cond/out group from sim type",
                "parameters": [
                    {"name": "sim_type_id", "in": "path", "required": True, "schema": {"type": "integer"}},
                    {"name": "cond_out_group_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/sim-types/{sim_type_id}/solvers": {
            "get": {
                "tags": ["relations"],
                "summary": "List sim type solvers",
                "parameters": [
                    {"name": "sim_type_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            },
            "post": {
                "tags": ["relations"],
                "summary": "Add solver to sim type",
                "parameters": [
                    {"name": "sim_type_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/SimTypeSolverRelCreateRequest"}}}
                },
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/sim-types/{sim_type_id}/solvers/{solver_id}/default": {
            "put": {
                "tags": ["relations"],
                "summary": "Set default solver for sim type",
                "parameters": [
                    {"name": "sim_type_id", "in": "path", "required": True, "schema": {"type": "integer"}},
                    {"name": "solver_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/v1/sim-types/{sim_type_id}/solvers/{solver_id}": {
            "delete": {
                "tags": ["relations"],
                "summary": "Remove solver from sim type",
                "parameters": [
                    {"name": "sim_type_id", "in": "path", "required": True, "schema": {"type": "integer"}},
                    {"name": "solver_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"$ref": "#/components/schemas/StandardResponse"}}
            }
        },
        "/api/projects": {
            "get": {
                "tags": ["projects"],
                "summary": "List projects (legacy)",
                "responses": {"200": {"description": "OK"}}
            },
            "post": {
                "tags": ["projects"],
                "summary": "Create project (legacy)",
                "security": [{"BearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"type": "object"}}}
                },
                "responses": {"201": {"description": "Created"}, "400": {"description": "Bad Request"}}
            }
        },
        "/api/projects/{project_id}": {
            "get": {
                "tags": ["projects"],
                "summary": "Get project (legacy)",
                "parameters": [
                    {"name": "project_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"description": "OK"}, "404": {"description": "Not found"}}
            },
            "put": {
                "tags": ["projects"],
                "summary": "Update project (legacy)",
                "security": [{"BearerAuth": []}],
                "parameters": [
                    {"name": "project_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"type": "object"}}}
                },
                "responses": {"200": {"description": "OK"}, "404": {"description": "Not found"}}
            },
            "delete": {
                "tags": ["projects"],
                "summary": "Delete project (legacy)",
                "security": [{"BearerAuth": []}],
                "parameters": [
                    {"name": "project_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"description": "OK"}, "404": {"description": "Not found"}}
            }
        },
        "/api/results/sim-type/{sim_type_result_id}": {
            "get": {
                "tags": ["results"],
                "summary": "Get sim type result",
                "security": [{"BearerAuth": []}],
                "parameters": [
                    {"name": "sim_type_result_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"description": "OK"}, "404": {"description": "Not found"}}
            }
        },
        "/api/results/order/{order_id}/sim-types": {
            "get": {
                "tags": ["results"],
                "summary": "Get order sim type results",
                "security": [{"BearerAuth": []}],
                "parameters": [
                    {"name": "order_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"description": "OK"}}
            }
        },
        "/api/results/sim-type/{sim_type_result_id}/rounds": {
            "get": {
                "tags": ["results"],
                "summary": "Get rounds with pagination",
                "security": [{"BearerAuth": []}],
                "parameters": [
                    {"name": "sim_type_result_id", "in": "path", "required": True, "schema": {"type": "integer"}},
                    {"name": "page", "in": "query", "required": False, "schema": {"type": "integer"}},
                    {"name": "pageSize", "in": "query", "required": False, "schema": {"type": "integer"}},
                    {"name": "status", "in": "query", "required": False, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"description": "OK"}}
            }
        },
        "/api/results/rounds/{round_id}": {
            "get": {
                "tags": ["results"],
                "summary": "Get round detail",
                "security": [{"BearerAuth": []}],
                "parameters": [
                    {"name": "round_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"description": "OK"}, "404": {"description": "Not found"}}
            }
        },
        "/api/results/analysis": {
            "post": {
                "tags": ["results"],
                "summary": "Analyze results",
                "security": [{"BearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/AnalysisRequest"}}}
                },
                "responses": {"200": {"description": "OK"}, "400": {"description": "Bad Request"}}
            }
        }
    }
}
