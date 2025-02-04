"""Testing EnrichedEventFacet objects of cbc_sdk.endpoint_standard"""

import pytest
import logging
from cbc_sdk.endpoint_standard import EnrichedEventFacet
from cbc_sdk.rest_api import CBCloudAPI
from cbc_sdk.base import FacetQuery
from cbc_sdk.errors import ApiError, TimeoutError
from tests.unit.fixtures.CBCSDKMock import CBCSDKMock
from tests.unit.fixtures.endpoint_standard.mock_enriched_events_facet import (
    POST_ENRICHED_EVENTS_FACET_SEARCH_JOB_RESP,
    GET_ENRICHED_EVENTS_FACET_SEARCH_JOB_RESULTS_RESP_1,
    GET_ENRICHED_EVENTS_FACET_SEARCH_JOB_RESULTS_RESP_2,
    GET_ENRICHED_EVENTS_FACET_SEARCH_JOB_RESULTS_RESP_STILL_QUERYING)

log = logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.DEBUG, filename='log.txt')


@pytest.fixture(scope="function")
def cb():
    """Create CBCloudAPI singleton"""
    return CBCloudAPI(url="https://example.com",
                      org_key="test",
                      token="abcd/1234",
                      ssl_verify=False)


@pytest.fixture(scope="function")
def cbcsdk_mock(monkeypatch, cb):
    """Mocks CBC SDK for unit tests"""
    return CBCSDKMock(monkeypatch, cb)


# ==================================== UNIT TESTS BELOW ====================================

def test_enriched_event_facet_select_where(cbcsdk_mock):
    """Testing EnrichedEvent Querying with select()"""
    cbcsdk_mock.mock_request("POST", "/api/investigate/v2/orgs/test/enriched_events/facet_jobs",
                             POST_ENRICHED_EVENTS_FACET_SEARCH_JOB_RESP)
    cbcsdk_mock.mock_request("GET",
                             "/api/investigate/v2/orgs/test/enriched_events/facet_jobs/08ffa932-b633-4107-ba56-8741e929e48b/results",  # noqa: E501
                             GET_ENRICHED_EVENTS_FACET_SEARCH_JOB_RESULTS_RESP_2)

    api = cbcsdk_mock.api
    events = api.select(EnrichedEventFacet).where(process_name="chrome.exe").add_facet_field("process_name")
    event = events.results
    assert event.terms is not None
    assert event.ranges is not None
    assert event.ranges == []
    assert event.terms[0]["field"] == "process_name"


def test_enriched_event_facet_select_async(cbcsdk_mock):
    """Testing EnrichedEvent Querying with select()"""
    cbcsdk_mock.mock_request("POST", "/api/investigate/v2/orgs/test/enriched_events/facet_jobs",
                             POST_ENRICHED_EVENTS_FACET_SEARCH_JOB_RESP)
    cbcsdk_mock.mock_request("GET",
                             "/api/investigate/v2/orgs/test/enriched_events/facet_jobs/08ffa932-b633-4107-ba56-8741e929e48b/results",  # noqa: E501
                             GET_ENRICHED_EVENTS_FACET_SEARCH_JOB_RESULTS_RESP_2)

    api = cbcsdk_mock.api
    future = api.select(EnrichedEventFacet).where(process_name="chrome.exe").add_facet_field(
        "process_name").execute_async()
    event = future.result()
    assert event.terms is not None
    assert event.ranges is not None
    assert event.ranges == []
    assert event.terms[0]["field"] == "process_name"


def test_enriched_event_facet_select_compound(cbcsdk_mock):
    """Testing EnrichedEvent Querying with select() and more complex criteria"""
    cbcsdk_mock.mock_request("POST", "/api/investigate/v2/orgs/test/enriched_events/facet_jobs",
                             POST_ENRICHED_EVENTS_FACET_SEARCH_JOB_RESP)
    cbcsdk_mock.mock_request("GET",
                             "/api/investigate/v2/orgs/test/enriched_events/facet_jobs/08ffa932-b633-4107-ba56-8741e929e48b/results",  # noqa: E501
                             GET_ENRICHED_EVENTS_FACET_SEARCH_JOB_RESULTS_RESP_2)

    api = cbcsdk_mock.api
    events = api.select(EnrichedEventFacet).where(process_name="chrome.exe").or_(
        process_name="firefox.exe").add_facet_field("process_name")
    event = events.results
    assert event.terms_.fields == ["process_name"]
    assert event.ranges == []


def test_enriched_event_facet_query_implementation(cbcsdk_mock):
    """Testing EnrichedEvent querying with where()."""
    cbcsdk_mock.mock_request("POST", "/api/investigate/v2/orgs/test/enriched_events/facet_jobs",
                             POST_ENRICHED_EVENTS_FACET_SEARCH_JOB_RESP)
    cbcsdk_mock.mock_request("GET",
                             "/api/investigate/v2/orgs/test/enriched_events/facet_jobs/08ffa932-b633-4107-ba56-8741e929e48b/results",  # noqa: E501
                             GET_ENRICHED_EVENTS_FACET_SEARCH_JOB_RESULTS_RESP_1)

    api = cbcsdk_mock.api
    field = 'process_name'
    events = api.select(EnrichedEventFacet).where(process_name="test").add_facet_field("process_name")
    assert isinstance(events, FacetQuery)
    event = events.results
    assert event.terms[0]["field"] == field
    assert event.terms_.facets["process_name"] is not None
    assert event.terms_.fields[0] == "process_name"
    assert event.ranges_.facets is not None
    assert event.ranges_.fields[0] == "device_timestamp"
    assert isinstance(event._query_implementation(api), FacetQuery)


def test_enriched_event_facet_timeout(cbcsdk_mock):
    """Testing EnrichedEventQuery.timeout()."""
    api = cbcsdk_mock.api
    query = api.select(EnrichedEventFacet).where("process_name:some_name").add_facet_field("process_name")
    assert query._timeout == 0
    query.timeout(msecs=500)
    assert query._timeout == 500


def test_enriched_event_facet_timeout_error(cbcsdk_mock):
    """Testing that a timeout in EnrichedEventQuery throws the right TimeoutError."""
    cbcsdk_mock.mock_request("POST", "/api/investigate/v2/orgs/test/enriched_events/facet_jobs",
                             POST_ENRICHED_EVENTS_FACET_SEARCH_JOB_RESP)
    cbcsdk_mock.mock_request("GET",
                             "/api/investigate/v2/orgs/test/enriched_events/facet_jobs/08ffa932-b633-4107-ba56-8741e929e48b/results",  # noqa: E501
                             GET_ENRICHED_EVENTS_FACET_SEARCH_JOB_RESULTS_RESP_STILL_QUERYING)

    api = cbcsdk_mock.api
    query = api.select(EnrichedEventFacet).where("process_name:some_name").add_facet_field("process_name").timeout(1)
    with pytest.raises(TimeoutError):
        query.results()
    query = api.select(EnrichedEventFacet).where("process_name:some_name").add_facet_field("process_name").timeout(1)
    with pytest.raises(TimeoutError):
        query._count()


def test_enriched_event_facet_query_add_range(cbcsdk_mock):
    """Testing EnrichedEvent results sort."""
    api = cbcsdk_mock.api
    range = {
        "bucket_size": 30,
        "start": "0D",
        "end": "20D",
        "field": "something"
    },
    events = api.select(EnrichedEventFacet).where(process_pid=1000).add_range(range).add_facet_field("process_name")
    assert events._ranges[0]["bucket_size"] == 30
    assert events._ranges[0]["start"] == "0D"
    assert events._ranges[0]["end"] == "20D"
    assert events._ranges[0]["field"] == "something"


def test_enriched_event_facet_query_check_range(cbcsdk_mock):
    """Testing EnrichedEvent results sort."""
    api = cbcsdk_mock.api
    range = {
        "bucket_size": [],
        "start": "0D",
        "end": "20D",
        "field": "something"
    },
    with pytest.raises(ApiError):
        api.select(EnrichedEventFacet).where(process_pid=1000).add_range(range).add_facet_field("process_name")

    range = {
        "bucket_size": 30,
        "start": [],
        "end": "20D",
        "field": "something"
    },
    with pytest.raises(ApiError):
        api.select(EnrichedEventFacet).where(process_pid=1000).add_range(range).add_facet_field("process_name")

    range = {
        "bucket_size": 30,
        "start": "0D",
        "end": [],
        "field": "something"
    },
    with pytest.raises(ApiError):
        api.select(EnrichedEventFacet).where(process_pid=1000).add_range(range).add_facet_field("process_name")

    range = {
        "bucket_size": 30,
        "start": "0D",
        "end": "20D",
        "field": []
    },
    with pytest.raises(ApiError):
        api.select(EnrichedEventFacet).where(process_pid=1000).add_range(range).add_facet_field("process_name")


def test_enriched_event_facet_query_add_facet_field(cbcsdk_mock):
    """Testing EnrichedEvent results sort."""
    api = cbcsdk_mock.api
    events = api.select(EnrichedEventFacet).where(process_pid=1000).add_facet_field("process_name")
    assert events._facet_fields[0] == "process_name"


def test_enriched_event_facet_query_add_facet_fields(cbcsdk_mock):
    """Testing EnrichedEvent results sort."""
    api = cbcsdk_mock.api
    events = api.select(EnrichedEventFacet).where(process_pid=1000).add_facet_field(["process_name", "process_pid"])
    assert "process_pid" in events._facet_fields
    assert "process_name" in events._facet_fields


def test_enriched_event_facet_query_add_facet_invalid_fields(cbcsdk_mock):
    """Testing EnrichedEvent results sort."""
    api = cbcsdk_mock.api
    with pytest.raises(TypeError):
        api.select(EnrichedEventFacet).where(process_pid=1000).add_facet_field(1337)


def test_enriched_event_facet_limit(cbcsdk_mock):
    """Testing EnrichedEvent results sort."""
    api = cbcsdk_mock.api
    events = api.select(EnrichedEventFacet).where(process_pid=1000).limit(123).add_facet_field("process_name")
    assert events._limit == 123


def test_enriched_event_facet_time_range(cbcsdk_mock):
    """Testing EnrichedEvent results sort."""
    api = cbcsdk_mock.api
    events = api.select(EnrichedEventFacet).where(process_pid=1000).set_time_range(start="2020-10-10T20:34:07Z",
                                                                                   end="2020-10-20T20:34:07Z",
                                                                                   window="-1d").add_facet_field(
        "process_name")
    assert events._time_range["start"] == "2020-10-10T20:34:07Z"
    assert events._time_range["end"] == "2020-10-20T20:34:07Z"
    assert events._time_range["window"] == "-1d"


def test_enriched_events_facet_submit(cbcsdk_mock):
    """Test _submit method of enrichedeventquery class"""
    cbcsdk_mock.mock_request("POST", "/api/investigate/v2/orgs/test/enriched_events/facet_jobs",
                             POST_ENRICHED_EVENTS_FACET_SEARCH_JOB_RESP)
    api = cbcsdk_mock.api
    events = api.select(EnrichedEventFacet).where(process_pid=1000).add_facet_field("process_name")
    events._submit()
    assert events._query_token == "08ffa932-b633-4107-ba56-8741e929e48b"


def test_enriched_events_facet_count(cbcsdk_mock):
    """Test _submit method of enrichedeventquery class"""
    cbcsdk_mock.mock_request("POST", "/api/investigate/v2/orgs/test/enriched_events/facet_jobs",
                             POST_ENRICHED_EVENTS_FACET_SEARCH_JOB_RESP)
    cbcsdk_mock.mock_request("GET",
                             "/api/investigate/v2/orgs/test/enriched_events/facet_jobs/08ffa932-b633-4107-ba56-8741e929e48b/results",  # noqa: E501
                             GET_ENRICHED_EVENTS_FACET_SEARCH_JOB_RESULTS_RESP_1)

    api = cbcsdk_mock.api
    events = api.select(EnrichedEventFacet).where(process_pid=1000).add_facet_field("process_name")
    events._count()
    assert events._count() == 116


def test_enriched_events_search(cbcsdk_mock):
    """Test _search method of enrichedeventquery class"""
    cbcsdk_mock.mock_request("POST", "/api/investigate/v2/orgs/test/enriched_events/facet_jobs",
                             POST_ENRICHED_EVENTS_FACET_SEARCH_JOB_RESP)
    cbcsdk_mock.mock_request("GET",
                             "/api/investigate/v2/orgs/test/enriched_events/facet_jobs/08ffa932-b633-4107-ba56-8741e929e48b/results",  # noqa: E501
                             GET_ENRICHED_EVENTS_FACET_SEARCH_JOB_RESULTS_RESP_2)

    api = cbcsdk_mock.api
    events = api.select(EnrichedEventFacet).where(process_pid=1000).add_facet_field("process_name")
    future = events.execute_async()
    result = future.result()
    assert result.terms is not None
    assert len(result.ranges) == 0
    assert result.terms[0]["field"] == "process_name"


def test_enriched_events_search_async(cbcsdk_mock):
    """Test _search method of enrichedeventquery class"""
    cbcsdk_mock.mock_request("POST", "/api/investigate/v2/orgs/test/enriched_events/facet_jobs",
                             POST_ENRICHED_EVENTS_FACET_SEARCH_JOB_RESP)
    cbcsdk_mock.mock_request("GET",
                             "/api/investigate/v2/orgs/test/enriched_events/facet_jobs/08ffa932-b633-4107-ba56-8741e929e48b/results",  # noqa: E501
                             GET_ENRICHED_EVENTS_FACET_SEARCH_JOB_RESULTS_RESP_2)

    api = cbcsdk_mock.api
    events = api.select(EnrichedEventFacet).where(process_pid=1000).add_facet_field("process_name")
    future = events.execute_async()
    result = future.result()
    assert result.terms is not None
    assert len(result.ranges) == 0
    assert result.terms[0]["field"] == "process_name"
