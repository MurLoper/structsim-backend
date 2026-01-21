from app.common.pagination import PageParams, PageResult


def test_page_params_from_request(app):
    with app.test_request_context('/api/v1/orders?page=0&page_size=999'):
        params = PageParams.from_request()
        assert params.page == 1
        assert params.page_size == 100
        assert params.offset == 0
        assert params.limit == 100


def test_page_result_properties():
    result = PageResult(items=[1, 2, 3], total=11, page=2, page_size=5)
    assert result.total_pages == 3
    assert result.has_next is True
    assert result.has_prev is True
    assert result.to_dict()['total'] == 11
