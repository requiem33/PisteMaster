export default {
    listTitle: 'Tournament List',
    createTitle: 'Start New Tournament',
    dashboard: {
        title: 'Tournament Console',
        tournamentStatus: 'Ongoing',
        editInfo: 'Edit Tournament Info',
        addEvent: 'Add Event',
        enterOrchestration: 'Enter Orchestration',
        stats: {
            totalEvents: 'Total Events',
            totalFencers: 'Registered Fencers',
            activePistes: 'Active Pistes',
            syncStatus: 'Sync Status',
            realtime: 'Realtime'
        },
        eventSection: 'Events',
        filterAll: 'All',
        filterIndividual: 'Individual',
        filterTeam: 'Team',
        noEvents: 'No events yet, click the top right button to create your first event',
        defaultRule: 'Default Rule',
        breadcrumb: {
            home: 'Home',
            tournamentList: 'Tournament List',
            currentTournament: 'Current Tournament'
        }
    },
    eventDrawer: {
        title: 'Create Event',
        form: {
            eventName: 'Event Name',
            eventType: 'Weapon Type',
            rule: 'Rule',
            eventNature: 'Event Type',
            startTime: 'Scheduled Start Time',
            individual: 'Individual',
            team: 'Team'
        },
        placeholder: {
            eventName: 'e.g., U14 Men\'s Epee Individual',
            eventType: 'Select Weapon Type',
            rule: 'Select Rule',
            startTime: 'Select Time'
        },
        alert: {
            title: 'Note',
            description: 'After creating the event, you will proceed to fencer registration and pool arrangement.'
        },
        messages: {
            eventNameRequired: 'Please enter event name',
            eventTypeRequired: 'Please select weapon type',
            ruleRequired: 'Please select rule',
            createSuccess: 'Event created successfully'
        },
        actions: {
            cancel: 'Cancel',
            confirmCreate: 'Confirm Create'
        }
    },
    form: {
        name: 'Tournament Name',
        organizer: 'Organizer',
        location: 'Location',
        date: 'Date',
        rangeSeparator: 'to',
        startPlaceholder: 'Start date',
        endPlaceholder: 'End date',
        rule: 'Rule',
        placeholder: {
            name: 'Enter tournament name',
            organizer: 'Enter organizer name',
            location: 'Enter location'
        }
    },
    messages: {
        nameRequired: 'Tournament name is required',
        dateRequired: 'Please select a date',
        createSuccess: 'Tournament created successfully',
        createFailed: 'Failed to create, please try again',
        deleteSuccess: 'Tournament deleted',
        deleteFailed: 'Delete failed',
        notFound: 'Tournament info not found',
        eventDeleteSuccess: 'Event deleted',
        eventDeleteFailed: 'Delete failed',
        eventCreateSuccess: 'Event created successfully',
        eventCreateFailed: 'Creation failed'
    },
    actions: {
        cancel: 'Cancel',
        createAndEnter: 'Create & Enter'
    },
    editDrawer: {
        title: 'Edit Tournament Info',
        updateSuccess: 'Tournament info updated',
        updateFailed: 'Update failed'
    },
    editEventDrawer: {
        title: 'Edit Event Info',
        updateSuccess: 'Updated successfully',
        updateFailed: 'Update failed'
    },
    confirm: {
        deleteTournament: 'Are you sure you want to permanently delete tournament "<strong>{name}</strong>"?<br/>This will also delete all events and results under this tournament, and cannot be undone.',
        deleteEvent: 'Are you sure you want to delete event "<strong>{name}</strong>"?<br/>This action cannot be undone.',
        confirmDelete: 'Confirm Delete',
        DangerConfirm: 'Dangerous Operation Confirm'
    }
}