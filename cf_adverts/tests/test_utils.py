import mock

from cf_adverts import utils


class TestUtils:

    uuid_mocked_result = '7d3bbb96-9145-4c2d-a4b8-a611010e18d8'

    def test_generate_random_str(self):
        result = utils.generate_random_str(length=20)
        assert len(result) == 20

    def test_str_method(self):
        result = utils.format_number(1234567)
        assert result == '1 234 567'

    @mock.patch('uuid.uuid4', return_value=uuid_mocked_result)
    def test_upload_path(self, mocked_f):
        result = utils.upload_path_handler(
            type('SomeCls', (), {'id': 10, 'FILE_PATH': 'images'})(),
            'test-file-name.txt'
        )
        assert result == 'images/10/{uuid}.txt'.format(
            uuid=self.uuid_mocked_result
        )

    @mock.patch('uuid.uuid4', return_value=uuid_mocked_result)
    def test_get_collected_amount_method(self, mocked_f):
        result = utils.uuid_replacer_handler(
            type('SomeCls', (), {'id': 10})(),
            'test-file-name.txt'
        )
        assert result == '10/{uuid}.txt'.format(uuid=self.uuid_mocked_result)
