from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.models.category import Category
from api.models.company import Company


class CategoryViewTests(APITestCase):
    # テスト用データのセットアップ
    def setUp(self):
        # 親カテゴリのないカテゴリ
        self.parent_category_company = Company.objects.create(name="Example Food Company")
        self.parent_category = Category.objects.create(company=self.parent_category_company, name="Food")

        # 親カテゴリのあるカテゴリ
        self.child_category_company = Company.objects.create(name="Example Fruits Company")
        self.child_category = Category.objects.create(company=self.child_category_company, name="Fruits", parent_category=self.parent_category)

        # カテゴリにない企業
        self.other_company = Company.objects.create(name="Other Company")


    # カテゴリ一覧の取得テスト
    def test_list(self):
        response = self.client.get(reverse("category-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["name"], "Food")
        self.assertEqual(response.data[1]["name"], "Fruits")

    # カテゴリ詳細の取得テスト
    def test_retrieve(self):
        response = self.client.get(reverse("category-detail", args=[self.parent_category.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.parent_category.id))
        self.assertEqual(response.data["name"], "Food")
        self.assertIsNone(response.data["parent_category"])

        response = self.client.get(reverse("category-detail", args=[self.child_category.id]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.child_category.id))
        self.assertEqual(response.data["name"], "Fruits")
        self.assertEqual(response.data["parent_category"], self.parent_category.id)

    # カテゴリの作成テスト
    def test_create(self):
        payload = {
            "company": str(self.other_company.id),
            "name": "Books",
            "parent_category": None,
        }
        
        self.assertFalse(Category.objects.filter(company=self.other_company, name="Books").exists())

        response = self.client.post(reverse("category-list"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Category.objects.filter(company=self.other_company, name="Books").exists())

    def test_create_duplication(self):
        payload = {
            "company": str(self.parent_category_company.id),
            "name": "Food",
            "parent_category": None,
        }
        
        self.assertTrue(Category.objects.filter(company=self.parent_category_company, name="Food").exists())

        response = self.client.post(reverse("category-list"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # カテゴリの更新テスト
    # 部分更新（PATCH）でカテゴリ名を変更
    def test_update_patch(self):        
        self.assertEqual(self.parent_category.name, "Food")

        payload = {"name": "Beverage"}
        response = self.client.patch(reverse("category-detail", args=[self.parent_category.id]), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.parent_category.refresh_from_db()
        self.assertEqual(self.parent_category.name, "Beverage")

    # 全体更新（PUT）でパッチを当ててもカテゴリ名が変更されないことを確認                
    def test_update_patch_by_put(self):
        self.assertEqual(self.parent_category.name, "Food")

        payload = { "name": "Beverage" }
        response = self.client.put(reverse("category-detail", args=[self.parent_category.id]), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.parent_category.refresh_from_db()
        self.assertEqual(self.parent_category.name, "Food")

    # 全体更新（PUT）でカテゴリ名を変更
    def test_update_put(self):
        payload = {
            "company": str(self.parent_category_company.id),
            "name": "Beverage",
            "parent_category": None,
        }
        response = self.client.put(reverse("category-detail", args=[self.parent_category.id]), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.parent_category.refresh_from_db()
        self.assertEqual(self.parent_category.name, "Beverage")


    # カテゴリの削除テスト
    def test_destroy(self):
        self.assertTrue(Category.objects.filter(id=self.parent_category.id).exists())

        response = self.client.delete(reverse("category-detail", args=[self.parent_category.id]))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Category.objects.filter(id=self.parent_category.id).exists())
