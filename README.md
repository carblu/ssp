<h2>Constrained Role Mining - Static Separation of Permission</h2>

<p aligh="justify">Role-based access control (RBAC) provides a framework for managing permissions in complex organizations by assigning users to roles, with each role determining the resources and operations accessible to its members. However, defining appropriate roles becomes challenging in environments with large numbers of users and resources. To address this issue, data mining techniques can be employed to automatically identify and propose candidate roles. The collection of methods and tools aimed at deriving roles from existing user–permission assignments is commonly referred to as *role mining*. In practice, role mining may also incorporate organizational constraints, such as cardinality restrictions and separation-of-duty requirements, to ensure that the resulting RBAC configuration can be effectively deployed and managed. These constraints simplify role administration and improve the overall maintainability of the access-control system.</p>

<p>
  We explore an alternative approach for incorporating constraints into the role-mining process. In particular, we focus on scenarios involving conflicting permissions, where specific predefined sets of permissions must not be assigned to the same role. We refer to this constraint as *Static Separation of Permissions* (SSP). Conceptually, SSP is closely related to *Static Separation of Duty* relations, which are commonly used in role-based systems to model conflicts of interest.
</p>

<p>
  Under the SSP framework, a user may still possess conflicting permissions, provided that these permissions are assigned through different roles. As a result, when accessing a protected resource that requires conflicting permissions, the user must activate and operate through distinct roles rather than a single combined role.
</p>
