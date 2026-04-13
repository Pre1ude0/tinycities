<script lang="ts">
	import { onMount } from 'svelte';

	function deleteCookie(name: string) {
		document.cookie = `${encodeURIComponent(name)}=; Path=/; Max-Age=0; SameSite=Lax`;
	}

	onMount(() => {
		deleteCookie('token');
		window.location.href = '/';
	});
</script>

<p>Logging out...</p>
