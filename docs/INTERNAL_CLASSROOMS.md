# Internal institute classrooms

An active institute Admin can use **Create classroom2**, immediately before the original Create classroom action. Both use the existing form. The new mode hides provider, public timetable and public publishing controls and explains that publishing is configured separately.

`api.create_internal_classroom` is POST-only and checks an enabled authenticated User and a real active Admin membership in the session institute, including for operator accounts. It rejects existing document names, client ownership/institute fields, public providers and any nonzero publishing value. The shared save implementation sets Institute ownership and forces `published=0` and an empty provider. Existing duration, document hooks, subscription request guards, enrollment and capacity logic are retained. No new schema is required.

Teacher assignment still requires an active Teacher member in this institute. Where institute directory profiles exist, the teacher must have an Active Teacher membership relationship to one of those profiles. This approval is teacher affiliation/consent, separate from the administrator owning a verified provider. Where no institute profile exists, the active local Teacher membership is the assignment authority. Teacher management rights recheck affiliation, so removing it does not leave management permissions behind. No relationship is invented or modified by creation.

Ordinary management of an existing unpublished, unlinked classroom preserves its internal state. Requesting public publishing takes the original verified-provider and publishing-authorization path. Internal classrooms match the existing Admin My classrooms filter (institute + Institute ownership + active); students still need enrollment and existing access gates.

## Local verification

1. Run the local backend against an explicitly authorized test database and start Vite. Sign in as an active institute Admin.
2. Open My classrooms. Confirm Create classroom2 appears immediately left of Create classroom. Teachers/students/inactive memberships must not receive this action.
3. Open Create classroom2, enter a title/subject and choose an already approved local teacher. Confirm no public-provider/timetable/publish controls appear.
4. Save; verify the room appears in My classrooms and is unpublished with no public provider, in the current institute. Verify ordinary internal edits work.
5. Try the original Create classroom flow; its provider checks still apply. Public publishing of the internal room must also require those checks.
6. A teacher without approved affiliation in a directory-backed institute is deliberately rejected; complete the existing consent workflow rather than bypassing it.

No shared preview database writes, migrations, deployment, or billing/identity changes were made for this feature. Pending publishing-delegation source from earlier work is preserved; its separate schema is not needed for internal classroom creation.
