# import unittest
# import uuid
#
# from app.core.Interfaces.campaign_interface import Campaign, CampaignRequest, Discount
#
# from app.core.classes.campaign_service import CampaignService
# from app.infra.campaign_in_memory_repository import CampaignInMemoryRepository
# from app.infra.product_in_memory_repository import DoesntExistError
#
#
# class TestCampaignService(unittest.TestCase):
#     def setUp(self):
#         # Create a real repository instance
#         self.repository = CampaignInMemoryRepository()
#         self.campaign_service = CampaignService()
#         self.campaign_service.repository = self.repository
#
#     def test_create_campaign(self):
#         # Arrange
#         campaign_request = CampaignRequest(
#             type="discount", data=Discount(product_id="123", discount_percentage=10)
#         )
#
#         # Act
#         result = self.campaign_service.create_campaign(campaign_request)
#
#         # Assert
#         self.assertEqual(result.type, campaign_request.type)
#         self.assertEqual(result.data, campaign_request.data)
#         self.assertIn(result.id, self.repository.campaigns)
#
#     def test_delete_campaign_success(self):
#         # Arrange
#         campaign_request = CampaignRequest(
#             type="discount", data=Discount(product_id="123", discount_percentage=10)
#         )
#         campaign = self.campaign_service.create_campaign(campaign_request)
#
#         # Act
#         self.campaign_service.delete_campaign(campaign.id)
#
#         # Assert
#         self.assertNotIn(campaign.id, self.repository.campaigns)
#
#     def test_delete_campaign_raises_error(self):
#         # Arrange
#         campaign_id = str(uuid.uuid4())
#
#         # Act & Assert
#         with self.assertRaises(DoesntExistError):
#             self.campaign_service.delete_campaign(campaign_id)
#
#     def test_read_all_campaigns(self):
#         # Arrange
#         campaign1 = self.campaign_service.create_campaign(
#             CampaignRequest(
#                 type="discount", data=Discount(product_id="123", discount_percentage=10)
#             )
#         )
#         campaign2 = self.campaign_service.create_campaign(
#             CampaignRequest(
#                 type="bonus", data=Discount(product_id="456", discount_percentage=20)
#             )
#         )
#
#         # Act
#         result = self.campaign_service.read_all_campaigns()
#
#         # Assert
#         self.assertEqual(len(result), 2)
#         self.assertIn(campaign1, result)
#         self.assertIn(campaign2, result)
