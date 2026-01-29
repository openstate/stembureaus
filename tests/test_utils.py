from tests.base_test_class import BaseTestClass

class TestRemovingUserConnectedToOneGemeente(BaseTestClass):
  AFFECTS_DB = True
  gemeente_code='GM0518'

  def setUp(self):
    super().setUp()
    from tests.utils import add_gemeente
    self.gemeente = add_gemeente(self, gemeente_code=self.gemeente_code)

    from tests.utils import add_user
    self.user1 = add_user(self, self.gemeente, "testuser1@openstate.eu")
    self.user2 = add_user(self, self.gemeente, "testuser2@openstate.eu")


  def test_remove(self):
    from tests.utils import get_gemeente_user, get_user
    from app.utils import remove_user, get_gemeente

    remove_user(self.user1)

    self.assertIsNotNone(get_gemeente(self.gemeente_code))
    self.assertIsNotNone(get_user(self.user2.email))
    self.assertIsNotNone(get_gemeente_user(self.user2, self.gemeente))
    self.assertIsNone(get_user(self.user1.email))
    self.assertIsNone(get_gemeente_user(self.user1, self.gemeente))


class TestRemovingUserConnectedToMultipleGemeenten(BaseTestClass):
  AFFECTS_DB = True
  gemeente_code1='GM0518' # 's-Gravenhage
  gemeente_code2='GM0106' # Assen

  def setUp(self):
    super().setUp()
    from tests.utils import add_gemeente, add_user_to_gemeente
    self.gemeente1 = add_gemeente(self, gemeente_code=self.gemeente_code1)
    self.gemeente2 = add_gemeente(self, gemeente_code=self.gemeente_code2, gemeente_naam="Assen")

    from tests.utils import add_user
    self.user1 = add_user(self, self.gemeente1, "testuser1@openstate.eu")
    add_user_to_gemeente(self, self.user1, self.gemeente2)
    self.user2 = add_user(self, self.gemeente1, "testuser2@openstate.eu")
    self.user3 = add_user(self, self.gemeente2, "testuser3@openstate.eu")


  def test_remove_from_one_gemeente(self):
    from tests.utils import get_gemeente_user, get_user
    from app.utils import remove_user_from_gemeente, get_gemeente

    remove_user_from_gemeente(self.user1, self.gemeente1)

    self.assertIsNotNone(get_gemeente(self.gemeente_code1))
    self.assertIsNotNone(get_gemeente(self.gemeente_code2))
    self.assertIsNotNone(get_user(self.user2.email))
    self.assertIsNotNone(get_gemeente_user(self.user2, self.gemeente1))
    self.assertIsNotNone(get_user(self.user3.email))
    self.assertIsNotNone(get_gemeente_user(self.user3, self.gemeente2))
    self.assertIsNotNone(get_user(self.user1.email))
    self.assertIsNotNone(get_gemeente_user(self.user1, self.gemeente2))
    self.assertIsNone(get_gemeente_user(self.user1, self.gemeente1))

  def test_remove_from_all_gemeenten(self):
    from tests.utils import get_gemeente_user, get_user
    from app.utils import remove_user, get_gemeente

    remove_user(self.user1)

    self.assertIsNotNone(get_gemeente(self.gemeente_code1))
    self.assertIsNotNone(get_gemeente(self.gemeente_code2))
    self.assertIsNotNone(get_user(self.user2.email))
    self.assertIsNotNone(get_gemeente_user(self.user2, self.gemeente1))
    self.assertIsNotNone(get_user(self.user3.email))
    self.assertIsNotNone(get_gemeente_user(self.user3, self.gemeente2))
    self.assertIsNone(get_user(self.user1.email))
    self.assertIsNone(get_gemeente_user(self.user1, self.gemeente1))
    self.assertIsNone(get_gemeente_user(self.user1, self.gemeente2))
