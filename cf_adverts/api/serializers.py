from rest_framework import serializers

from .. import models


class ProjectShortSerializer(serializers.ModelSerializer):
    small_logo = serializers.SerializerMethodField(read_only=True)

    def get_small_logo(self, obj):
        if obj.small_logo:
            return obj.small_logo['small'].url

    class Meta:
        model = models.Advert
        fields = (
            'id',
            'title',
            'small_logo',
            'ended_at',
            'total_amount',
            'collected_amount',
            'get_collected_percent',
            'short_description',
            'has_draft',
            'expired_at'
        )
        extra_kwargs = {
            'get_collected_percent': {'read_only': True},
            'has_draft': {'read_only': True},
            'expired_at': {'read_only': True, 'source': 'get_expired_at'},
        }


class EstimateCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.AdvertEstimate
        fields = (
            'id',
            'advert',
            'title',
            'amount',
        )


class EstimateDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.AdvertEstimate
        fields = (
            'id',
            'title',
            'amount',
        )


class EstimateListUpdateSerializer(EstimateDetailSerializer):

    id = serializers.IntegerField(required=False)

    def create(self, validated_data):
        instance = None
        if 'id' in validated_data:
            instance = self.Meta.model.objects.filter(
                id=validated_data['id']).last()

        if instance:
            self.instance = instance
            return self.update(instance, validated_data)
        else:
            return super(EstimateListUpdateSerializer, self).create(validated_data)


class AdvertListDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Advert
        fields = (
            'id',
            'title',
            'category',
            'small_logo',
            'location',
            'short_description',
            'ended_at',
            'total_amount',
            'collected_amount',
            'get_collected_percent',
            'expired_at',
        )

        extra_kwargs = {
            'get_collected_percent': {'read_only': True},
            'has_draft': {'read_only': True},
            'expired_at': {'read_only': True, 'source': 'get_expired_at'},
        }


class AdvertCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Advert
        fields = (
            'id',
            'title',
            'category',
            'logo',
            'small_logo',
            'location',
            'short_description',
            'total_amount'
        )
        extra_kwargs = {
            'title': {'required': True},
            'category': {'required': True},
            'logo': {'required': True},
            'small_logo': {'required': True},
            'location': {'required': True},
            'short_description': {'required': True},
            'total_amount': {'required': True},
        }


class AdvertUpdateSerializer(serializers.ModelSerializer):

    preview = serializers.SerializerMethodField(read_only=True)

    def get_preview(self, obj):
        if obj.logo:
            return obj.logo['small'].url

    class Meta:
        model = models.Advert
        fields = (
            'id',
            'title',
            'preview',
            'origin_id',
            'category',
            'video',
            'logo',
            'small_logo',
            'location',
            'status',
            'short_description',
            'description',
            'ended_at',
            'is_draft',
            'is_available',
            'total_amount',
            'collected_amount',
            'has_draft',
            'get_collected_percent',
            'articles_of_association',
            'articles_of_association_approved',
            'extract_from_egrul',
            'extract_from_egrul_approved',
            'general_meeting_decision',
            'general_meeting_decision_approved',
            'expired_at',
        )
        extra_kwargs = {
            'articles_of_association_approved': {'read_only': True},
            'category': {'required': False},
            'collected_amount': {'read_only': True},
            'ended_at': {'read_only': True},
            'expired_at': {'read_only': True, 'source': 'get_expired_at'},
            'extract_from_egrul_approved': {'read_only': True},
            'get_collected_percent': {'read_only': True},
            'general_meeting_decision_approved': {'read_only': True},
            'has_draft': {'read_only': True},
            'is_available': {'read_only': True},
            'is_draft': {'read_only': True},
            'logo': {'required': False, 'allow_null': False},
            'origin_id': {'read_only': True},
            'status': {'read_only': True},
            'small_logo': {'required': False, 'allow_null': False},
        }


class AdvertDetailSerializer(serializers.ModelSerializer):
    preview = serializers.SerializerMethodField(read_only=True)
    estimates = EstimateDetailSerializer(many=True, read_only=True)

    def get_preview(self, obj):
        if obj.logo:
            return obj.logo['small'].url

    class Meta:
        model = models.Advert
        fields = (
            'id',
            'title',
            'origin_id',
            'get_collected_percent',
            'category',
            'location',
            'status',
            'short_description',
            'preview',
            'description',
            'logo',
            'small_logo',
            'video',
            'ended_at',
            'is_draft',
            'total_amount',
            'collected_amount',
            'is_available',
            'has_draft',
            'articles_of_association',
            'extract_from_egrul',
            'general_meeting_decision',
            'articles_of_association_approved',
            'extract_from_egrul_approved',
            'general_meeting_decision_approved',
            'expired_at',
            'estimates'
        )
        extra_kwargs = {
            'draft_status': {'read_only': True, 'source': 'get_draft_status'},
            'expired_at': {'read_only': True, 'source': 'get_expired_at'}
        }


class ProjectEventSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Event
        fields = ('id', 'base_type', 'percent', 'description', 'created')
