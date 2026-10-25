# 第一步: 先建一个基础员工类
class Employee:
    def __init__(self,name,id):
        self.name = name
        self.id = id


    def print_info(self):
        print(f"员工名字: {self.name}, 工号: {self.id}")


# 第二步: 建全职员工类，括号里写 Employee 表示“继承”
class FulltimeEmployee(Employee):
    def __init__(self, name, id, monthly_salary):
        super().__init__(name,id)
        self.monthly_salary = monthly_salary


# 第三步: 造一个活人
zhangsan = FulltimeEmployee("张三","1001",6000)


# 第四步: 按一下他胸口的按钮
zhangsan.print_info()


# 兼职员工也有姓名和工号，所以括号里还是填 Employee
class ParttimeEmployee(Employee):
    def __init__(self, name, id, daily_salary,work_days):
        super().__init__(name,id)
        # 存兼职专属的属性 （日薪和工作天数）
        self.daily_salary = daily_salary
        self.work_days = work_days

        # Employee 没有算工资的能力，所以我们在兼职类自己写一个
    def calculate_monthly_pay(self):
        return self.daily_salary * self.work_days


# 造一个兼职工李四‘
lisi = ParttimeEmployee("李四", "1002", 230, 15)
lisi.print_info()


# 算一下李四的工资并打印出来
print(f"李四的工资是: {lisi.calculate_monthly_pay()}元")